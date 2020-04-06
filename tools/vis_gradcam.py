import argparse
import os
import pprint
import shutil
import sys

import logging
import time
import timeit
from pathlib import Path

import cv2
import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn

import _init_paths
import models
import datasets
from config import config
from config import update_config
from core.function import testval
from utils.gradcam import SegGradCAM
from utils.modelsummary import get_model_summary
from utils.utils import create_logger

def parse_args():
    parser = argparse.ArgumentParser(description='Visualize GradCAM')
    
    parser.add_argument('--cfg',
                        help='experiment configure file name',
                        required=True,
                        type=str)
    parser.add_argument('--image-index', type=int, default=0,
                        help='Index of input image for GradCAM')
    parser.add_argument('--pixel-i', type=int, default=0, 
                        help='i coordinate of pixel from which to compute GradCAM')
    parser.add_argument('--pixel-j', type=int, default=0, 
                        help='j coordinate of pixel from which to compute GradCAM')
    parser.add_argument('--target-layer', type=str,
                        help='Target layer from which to compute GradCAM')
    parser.add_argument('opts',
                        help="Modify config options using the command-line",
                        default=None,
                        nargs=argparse.REMAINDER)

    args = parser.parse_args()
    update_config(config, args)

    return args

def retrieve_raw_image(dataset, index):
    item = dataset.files[index]
    image = cv2.imread(os.path.join(dataset.root,'cityscapes',item["img"]),
                       cv2.IMREAD_COLOR)
    return image

def save_gradcam(save_path, gradcam, raw_image, paper_cmap=False):
    gradcam = gradcam.cpu().numpy()
    cmap = cm.jet_r(gradcam)[..., :3] * 255.0
    if paper_cmap:
        alpha = gradcam[..., None]
        gradcam = alpha * cmap + (1 - alpha) * raw_image
    else:
        gradcam = (cmap.astype(np.float) + raw_image.astype(np.float)) / 2
    cv2.imwrite(save_path, np.uint8(gradcam))

def main():
    args = parse_args()

    logger, final_output_dir, _ = create_logger(
        config, args.cfg, 'vis_gradcam')

    logger.info(pprint.pformat(args))
    logger.info(pprint.pformat(config))

    # cudnn related setting
    cudnn.benchmark = config.CUDNN.BENCHMARK
    cudnn.deterministic = config.CUDNN.DETERMINISTIC
    cudnn.enabled = config.CUDNN.ENABLED

    # build model
    model = eval('models.'+config.MODEL.NAME +
                 '.get_seg_model')(config)

    dump_input = torch.rand(
        (1, 3, config.TRAIN.IMAGE_SIZE[1], config.TRAIN.IMAGE_SIZE[0])
    )
    logger.info(get_model_summary(model.cuda(), dump_input.cuda()))

    if config.TEST.MODEL_FILE:
        model_state_file = config.TEST.MODEL_FILE
    else:
        model_state_file = os.path.join(final_output_dir,
                                        'best.pth')
    logger.info('=> loading model from {}'.format(model_state_file))
        
    pretrained_dict = torch.load(model_state_file)
    model_dict = model.state_dict()
    pretrained_dict = {k[6:]: v for k, v in pretrained_dict.items()
                        if k[6:] in model_dict.keys()}
    for k, _ in pretrained_dict.items():
        logger.info(
            '=> loading {} from pretrained model'.format(k))
    model_dict.update(pretrained_dict)
    model.load_state_dict(model_dict)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device).eval()

    # Retrieve input image corresponding to args.image_index
    test_size = (config.TEST.IMAGE_SIZE[1], config.TEST.IMAGE_SIZE[0])
    assert args.pixel_i < test_size[0] and args.pixel_j < test_size[1], \
        "Pixel ({},{}) is out of bounds for image of size ({},{})".format(
            args.pixel_i,args.pixel_j,test_size[0],test_size[1])
    test_dataset = eval('datasets.'+config.DATASET.DATASET)(
                        root=config.DATASET.ROOT,
                        list_path=config.DATASET.TEST_SET,
                        num_samples=None,
                        num_classes=config.DATASET.NUM_CLASSES,
                        multi_scale=False,
                        flip=False,
                        ignore_label=config.TRAIN.IGNORE_LABEL,
                        base_size=config.TEST.BASE_SIZE,
                        crop_size=test_size,
                        downsample_rate=1)
    image,_,_,name = test_dataset[args.image_index]
    image = torch.from_numpy(image).unsqueeze(0).to(device)
    logger.info("Using image {}...".format(name))

    # Define target layer
    if args.target_layer:
        target_layer = args.target_layer
    else:
        for name, module in self.model.named_modules()[::-1]:
            if 'conv' in name:
                target_layer = name
            break
    logger.info('Target layer set to {}'.format(target_layer))

    # Run forward + backward passes
    gradcam_args = [args.image_index, args.pixel_i, args.pixel_j]
    logger.info('Running GradCAM on image {} at pixel ({},{})...'.format(*gradcam_args))
    gradcam = SegGradCAM(model=model, candidate_layers=[target_layer])
    pred_probs, pred_labels = gradcam.forward(image)
    gradcam.backward(pred_labels[:,[0],:,:], args.pixel_i, args.pixel_j)

    # Generate GradCAM + save heatmap
    gradcam_region = gradcam.generate(target_layer=target_layer)[0,0]
    save_path = os.path.join(final_output_dir, 
        'gradcam-image-{}-pixel_i-{}-pixel_j-{}'.format(*gradcam_args))
    raw_image = retrieve_raw_image(test_dataset, args.image_index)
    logger.info('Saving GradCAM heatmap at {}...'.format(save_path))
    save_gradcam(save_path, gradcam_region, raw_image)


if __name__ == '__main__':
    main()
