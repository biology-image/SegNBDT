# SegNBDT: Visual Decision Rules for Segmentation

[Project Page](http://segnbdt.aaalv.in) &nbsp;//&nbsp; [Paper](https://arxiv.org/abs/2006.06868)

*By \*Alvin Wan, \*Daniel Ho, Younjin Song, Henk Tillman, Sarah Adel Bargal, Joseph E. Gonzalez*

<sub>*denotes equal contribution</sub>

Run neural-backed decision trees that achieve competitive accuracy within ~2-4% of the state-of-the-art HRNetV2 segmentation model on three benchmark datasets -- Cityscapes, Pascal-Context, and LookIntoPerson. Run Gradient-weighted Pixel Activation Mapping (GradPAM) and Semantic Input Removal (SIR) for coarse and fine-grained visual decision rules respectively.

Note that this repository is based on the [HRNetV2](https://github.com/HRNet/HRNet-Semantic-Segmentation/tree/pytorch-v1.1) repository and modified for our purposes.

![grad_pam_pipeline](https://user-images.githubusercontent.com/14956645/83956574-6bd2a280-a814-11ea-8f8d-599cf19aa7dd.jpg)

**Table of Contents**

- [Quickstart: Installation, Running, and Loading](#quickstart)
- [Convert your own neural network into a decision tree](#convert-neural-networks-to-decision-trees)
- [Training and Evaluation](#training-and-evaluation)
- [Visualization](#visualization)
- [Results](#results)
- [Citation](#citation)

# Quickstart

## Installation

1. Pip install [nbdt](https://github.com/alvinwan/neural-backed-decision-trees):
```bash
git clone https://github.com/alvinwan/neural-backed-decision-trees
pip install nbdt
```
2. Clone this repository and install all dependencies:
```bash
git clone https://github.com/daniel-ho/SegNBDT
pip install -r requirements.txt
```
Note: This repository has only been tested with Python 3.6.

## Dataset Preparation

<details><summary><b>Cityscapes Setup</b> <i>[click to expand]</i></summary>
<div>

1. Create a Cityscapes account [here](https://www.cityscapes-dataset.com/).
2. Download the following:
	- Images (leftImg8bit_trainvaltest.zip)
	- Annotations (gtFine_trainvaltest.zip)

</div>
</details>

<details><summary><b>Pascal-Context Setup</b> <i>[click to expand]</i></summary>
<div>

To download Pascal-Context, run the following command from the `SegNBDT` directory:

```bash
python data/scripts/download_pascal_ctx.py
```

The above script performs the following:
- Install [Detail API](https://github.com/zhanghang1989/detail-api) for parsing Pascal-Context
- Download Pascal VOC 2010 dataset
- Download Pascal-Context files
    - trainval_merged.json
    - train.pth
    - val.pth

</div>
</details>

<details><summary><b>Look Into Person Setup</b> <i>[click to expand]</i></summary>
<div>

Download the (Single Person) Look Into Person dataset [here](http://sysu-hcp.net/lip/overview.php).

The following zip files are required:
- TrainVal_images.zip
- TrainVal_parsing_annotations.zip
- Train_parsing_reversed_labels.zip

</div>
</details>

<details><summary><b>ADE20K Scene Parsing Setup</b> <i>[click to expand]</i></summary>
<div>

Download the ADE20K Scene Parsing dataset [here](http://sceneparsing.csail.mit.edu/).
Alternatively, run the following:
```bash
wget http://data.csail.mit.edu/places/ADEchallenge/ADEChallengeData2016.zip
```

</div>
</details>

The dataset directory will look as follows:
````
SegNBDT/data
├── cityscapes
│   ├── gtFine
│   │   ├── test
│   │   ├── train
│   │   └── val
│   └── leftImg8bit
│       ├── test
│       ├── train
│       └── val
├── pascal_ctx
│   ├── common
│   ├── PythonAPI
│   ├── res
│   └── VOCdevkit
│       └── VOC2010
├── lip
│   ├── TrainVal_images
│   │   ├── train_images
│   │   └── val_images
│   └── TrainVal_parsing_annotations
│       ├── train_segmentations
│       ├── train_segmentations_reversed
│       └── val_segmentations
├── ade20k
│   ├── annotations
│   │   ├── training
│   │   └── validation
│   ├── images
│   │   ├── training
│   │   └── validation
│   ├── objectInfo150.txt
│   └── sceneCategories.txt
├── list
│   ├── cityscapes
│   │   ├── test.lst
│   │   ├── trainval.lst
│   │   └── val.lst
│   ├── lip
│   │   ├── testvalList.txt
│   │   ├── trainList.txt
│   │   └── valList.txt
│   └── ade20k
│       ├── training.odgt
│       └── validation.odgt
````

# Convert Neural Networks to Decision Trees

**To convert your neural network** into a neural-backed decision tree for segmentation:

1. **Download or train baseline segmentation model**. No modifications are necessary for training the baseline model.

2. **Generate induced hierarchy using pretrained model**.

  ```bash
  nbdt-hierarchy --checkpoint=${CHECKPOINT}.pth --dataset=${DATASET}
  ```

3. **Setup experiment configuration file**. Existing configuration files for baseline models can be modified for training NBDT models by adding the lines below. In the example below, we modify the HRNetv2-W18-v1 configuration file by specifying the dataset, induced hierarchy name, and tree supervision weight.

  ```
  NBDT:
    USE_NBDT: true
    DATASET: 'Cityscapes'
    HIERARCHY: 'induced-HRNet-w18-v1'
    TSW: 10
  ```

4. **Train the original neural network with an NBDT loss**. Wrap the original criterion with the NBDT loss. In the example below, we assume the original loss is denoted by `criterion`.

  ```python
  from nbdt.loss import SoftSegTreeSupLoss
  criterion = SoftSegTreeSupLoss(config.NBDT.DATASET, criterion,
      hierarchy=config.NBDT.HIERARCHY, tree_supervision_weight=config.NBDT.TSW)
  ```

5. **Perform inference or validate using an NBDT model**. Wrap the original model trained in the previous step. In the example below, the original model is denoted by `model` and it is wrapped with the SoftSegNBDT wrapper.

  ```python
  from nbdt.model import SoftSegNBDT
  model = SoftSegNBDT(config.NBDT.DATASET, model, hierarchy=config.NBDT.HIERARCHY)
  ```

<details><summary><b>Want to train on a new dataset?</b> <i>[click to expand]</i></summary>
<div>

In order to support a new dataset, changes must be made to the NBDT repository. Follow the same steps as in the NBDT repository, located [here](https://github.com/alvinwan/neural-backed-decision-trees#dataset). Note that the NBDT repository must be setup in development mode for the changes to be reflected. At a high-level, the following steps must be completed:
- Add dataloader for new dataset in `nbdt/data`
- Modify `nbdt/utils.py` to support the new dataset
- Optionally generate wnids for the dataset (hardcodings may be needed in `nbdt/bin/nbdt-wnids`)

</div>
</details>

# Training and Evaluation

Pretrained models for the baselines and NBDT models are provided [here](https://github.com/daniel-ho/SegNBDT/releases/tag/0.0.1). To use these checkpoints, specify the checkpoint path using the configuration `TEST.MODEL_FILE`. To train from scratch, download the models pretrained on ImageNet [here](https://github.com/HRNet/HRNet-Image-Classification). The ImageNet pretrained models must be placed in a `pretrained_models` directory in the repository.

For both training and evaluation, a configuration file must be specified. Configuration files for training baseline models can be found under `experiments/${DATASET}`, while the configuration files for training NBDT models can be found under `experiments/${DATASET}/nbdt`. In general, the provided configuration files assume 4 GPUs unless otherwise specified.

## Training

The command to train a baseline model on 4 GPUs will follow this format:
```
python -m torch.distributed.launch --nproc_per_node=4 tools/train.py --cfg experiments/${DATASET}/${CONFIG}.yaml
```

For example, the following command trains a baseline HRNetv2-W48 model on Cityscapes:
```
python -m torch.distributed.launch --nproc_per_node=4 tools/train.py --cfg experiments/cityscapes/seg_hrnet_w48_train_512x1024_sgd_lr1e-2_wd5e-4_bs_12_epoch484.yaml
```

The command to train an NBDT model is almost identical. For example:
```
python -m torch.distributed.launch --nproc_per_node=4 tools/train.py --cfg experiments/cityscapes/nbdt/seg_hrnet_w48_train_512x1024_sgd_lr1e-2_wd5e-4_bs_12_epoch484_tsw10.yaml
```

## Evaluation

The evaluation command follows this format:
```
python tools/test.py --cfg experiments/${DATASET}/${CONFIG}.yaml TEST.MODEL_FILE ${CHECKPOINT_PATH}
```
If `TEST.MODEL_FILE` is not specified, by default, evaluation will load the checkpoint located at `output/${DATASET}/${CONFIG}/best.pth`. Otherwise, `TEST.MODEL_FILE` can be used to load pretrained checkpoints.

Evaluating baseline Cityscapes model without multi-scale and flip testing:
```
python tools/test.py --cfg experiments/cityscapes/seg_hrnet_w48_train_512x1024_sgd_lr1e-2_wd5e-4_bs_12_epoch484.yaml
```

Evaluating NBDT Cityscapes model without multi-scale and flip testing:
```
python tools/test.py --cfg experiments/cityscapes/nbdt/seg_hrnet_w48_train_512x1024_sgd_lr1e-2_wd5e-4_bs_12_epoch484_tsw10.yaml
```

Evaluating baseline Pascal-Context with multi-scale and flip testing:
```
python tools/test.py --cfg experiments/pascal_ctx/seg_hrnet_w48_cls59_480x480_sgd_lr4e-3_wd1e-4_bs_16_epoch200.yaml \
                     TEST.SCALE_LIST 0.5,0.75,1.0,1.25,1.5,1.75,2.0 \
                     TEST.FLIP_TEST True
```

Evaluating baseline LookIntoPerson with flip testing:
```
python tools/test.py --cfg experiments/lip/seg_hrnet_w48_473x473_sgd_lr7e-3_wd5e-4_bs_40_epoch150.yaml \
                     DATASET.TEST_SET list/lip/testvalList.txt \
                     TEST.FLIP_TEST True \
                     TEST.NUM_SAMPLES 0
```

# Visualization

## Coarse Visual Decision Rules: GradPAM

Configuration files for visualizations are located under `experiments/cityscapes/vis/*`. Note that the visualization configurations are identical to their training configuration counterpart aside from number of GPUs used. For example, `experiments/cityscapes/vis/vis_seg_hrnet_w18_small_v1_512x1024_tsw10.yaml` is the same as `experiments/cityscapes/nbdt/seg_hrnet_w18_small_v1_512x1024_sgd_lr1e-2_wd5e-4_bs_12_epoch484_tsw10.yaml`. Thus to generate visualizations for other datasets, the configurations can simply be copy and pasted.

How to generate image-wide GradPAM. Got a node, class, and image in mind?

```
python tools/vis_gradcam.py \
	--cfg experiments/cityscapes/vis/vis_seg_hrnet_w18_small_v1_512x1024_tsw10.yaml \
	--vis-mode GradPAMWhole \
	--image-index-range 0 5 1 \
	--nbdt-node-wnid n00002684 \
	--skip-save-npy \
	--target-layers last_layer.3 \
		TEST.MODEL_FILE output/cityscapes/seg_hrnet_w18_small_v1_512x1024_sgd_lr1e-2_wd5e-4_bs_12_epoch484_tsw10/best.pth \
		NBDT.USE_NBDT True;
```

How to generate SegNBDT visual decision rules + GradPAMS. Got a class in mind? Automatically find nodes for that class and run over many images.

<details>
	<summary>1. Generate saliency maps</summary>

NBDT
```
for cls in car building vegetation bus sidewalk rider wall bicycle sky traffic_light; do
	python tools/vis_gradcam.py \
			--cfg experiments/cityscapes/vis/vis_seg_hrnet_w18_small_v1_512x1024_tsw10.yaml \
			--vis-mode GradPAMWhole \
			--crop-size 400 \
			--pixel-max-num-random 1 \
			--image-index-range 0 200 1 \
			--nbdt-node-wnids-for ${cls} \
			--crop-for ${cls} \
			--skip-save-npy \
			--target-layers last_layer.3 \
				TEST.MODEL_FILE output/cityscapes/seg_hrnet_w18_small_v1_512x1024_sgd_lr1e-2_wd5e-4_bs_12_epoch484_tsw10/best.pth \
				NBDT.USE_NBDT True;
done;
```
baseline
```
for cls in car building vegetation bus sidewalk rider wall bicycle sky traffic_light; do
		python tools/vis_gradcam.py \
				--cfg experiments/cityscapes/vis/vis_seg_hrnet_w18_small_v1_512x1024.yaml \
				--vis-mode SegGradCAM \
				--crop-size 400 \
				--pixel-max-num-random 1 \
				--image-index-range 0 250 1 \
				--crop-for ${cls} \
				--skip-save-npy \
				--target-layers last_layer.3 \
					TEST.MODEL_FILE output/cityscapes/seg_hrnet_w18_small_v1_512x1024_sgd_lr1e-2_wd5e-4_bs_12_epoch484_tsw10/best.pth
done;
```

</details>

<details>
	<summary>2. Generate templates</summary>

```
nbdt-hierarchy \
		--path graph-induced-hrnet_w18_small_v1_cityscapes_cls19_1024x2048_trainset.json \
		--vis-no-color-leaves \
		--vis-out-fname template \
		--vis-hide f00000030 f00000031 f00000034 \
		--vis-node-conf f00000032 below.dy 300 \
		--vis-node-conf f00000032 below.href '{{ f00000032 }}' \
		--vis-node-conf f00000032 below.label '5. Car? Yes.' \
		--vis-node-conf f00000032 below.sublabel 'Finds headlights, tires' \
		--vis-node-conf f00000033 below.href '{{ f00000033 }}' \
		--vis-node-conf f00000033 below.label '4. Pavement? No.' \
		--vis-node-conf f00000035 below.dy 250 \
		--vis-node-conf f00000035 below.href '{{ f00000035 }}' \
		--vis-node-conf f00000035 below.label '3. Landscape? No.' \
		--vis-node-conf f00000036 below.dy 250 \
		--vis-node-conf f00000036 below.href '{{ f00000036 }}' \
		--vis-node-conf f00000036 below.label '2. Road? No.' \
		--vis-node-conf f00000036 left.href '{{ original }}' \
		--vis-node-conf f00000036 left.label '1. Start here' \
		--vis-node-conf f00000036 left.sublabel 'Goal: Classify center pixel' \
		--vis-zoom 1.75 \
		--vis-color-path-to car \
		--vis-below-dy 375 \
		--vis-scale 0.8 \
		--vis-margin-top -125 \
		--vis-height 500 \
		--vis-width 900
```

```
nbdt-hierarchy \
		--path graph-induced-hrnet_w18_small_v1_cityscapes_cls19_1024x2048_trainset.json \
		--vis-no-color-leaves \
		--vis-out-fname template \
		--vis-hide f00000033 \
		--vis-node-conf f00000034 below.href '{{ f00000034 }}' \
		--vis-node-conf f00000034 below.label '4. Building? Yes.' \
		--vis-node-conf f00000035 below.href '{{ f00000035 }}' \
		--vis-node-conf f00000035 below.label '3. Landscape? Yes.' \
		--vis-node-conf f00000036 below.href '{{ f00000036 }}' \
		--vis-node-conf f00000036 below.label '2. Road? No.' \
		--vis-node-conf f00000036 left.href '{{ original }}' \
		--vis-node-conf f00000036 left.label '1. Start here' \
		--vis-node-conf f00000036 left.sublabel 'Goal: Classify center pixel' \
		--vis-zoom 1.75 \
		--vis-color-path-to building \
		--vis-below-dy 250 \
		--vis-scale 0.8 \
		--vis-margin-top -50 \
		--vis-height 450 \
		--vis-width 800
```

```
nbdt-hierarchy \
		--path graph-induced-hrnet_w18_small_v1_cityscapes_cls19_1024x2048_trainset.json \
		--vis-no-color-leaves \
		--vis-out-fname template \
    --vis-root f00000031 \
		--vis-hide n00002684 f00000028 \
		--vis-node-conf f00000031 below.href '{{ f00000031 }}' \
		--vis-node-conf f00000031 below.label '2. Person or bike? No.' \
		--vis-node-conf f00000031 below.sublabel 'Looks for person, wheel' \
		--vis-node-conf f00000029 below.href '{{ f00000029 }}' \
		--vis-node-conf f00000029 below.label '3. Pole-like? No.' \
		--vis-node-conf n03100490 below.dy 350 \
		--vis-node-conf n03100490 below.href '{{ n03100490 }}' \
		--vis-node-conf n03100490 below.label '4. Truck? No.' \
		--vis-node-conf n04019101 below.href '{{ n04019101 }}' \
		--vis-node-conf n04019101 below.label '5. Bus? Yes.' \
		--vis-node-conf f00000031 left.href '{{ original }}' \
		--vis-node-conf f00000031 left.label '1. Start here' \
		--vis-node-conf f00000031 left.sublabel 'Goal: Classify center pixel' \
		--vis-zoom 1.75 \
		--vis-color-path-to bus \
		--vis-below-dy 250 \
		--vis-scale 0.8 \
		--vis-margin-top -125 \
		--vis-height 500 \
		--vis-width 800
```

```
nbdt-hierarchy \
		--path graph-induced-hrnet_w18_small_v1_cityscapes_cls19_1024x2048_trainset.json \
		--vis-no-color-leaves \
		--vis-out-fname template \
		--vis-hide f00000032 n00001930 f00000034 \
		--vis-node-conf f00000030 below.dy 400 \
		--vis-node-conf f00000030 below.href '{{ f00000030 }}' \
		--vis-node-conf f00000030 below.label '5. Sidewalk? Yes.' \
		--vis-node-conf f00000033 below.dy 350 \
		--vis-node-conf f00000033 below.href '{{ f00000033 }}' \
		--vis-node-conf f00000033 below.label '4. Pavement? Yes.' \
		--vis-node-conf f00000035 below.href '{{ f00000035 }}' \
		--vis-node-conf f00000035 below.label '3. Landscape? No.' \
		--vis-node-conf f00000036 below.href '{{ f00000036 }}' \
		--vis-node-conf f00000036 below.label '2. Road? No.' \
		--vis-node-conf f00000036 left.href '{{ original }}' \
		--vis-node-conf f00000036 left.label '1. Start here' \
		--vis-node-conf f00000036 left.sublabel 'Goal: Classify center pixel' \
		--vis-zoom 1.75 \
		--vis-color-path-to sidewalk \
		--vis-below-dy 250 \
		--vis-scale 0.8 \
		--vis-margin-top -125 \
		--vis-height 500 \
		--vis-width 900
```

```
nbdt-hierarchy \
		--path graph-induced-hrnet_w18_small_v1_cityscapes_cls19_1024x2048_trainset.json \
		--vis-no-color-leaves \
		--vis-out-fname template \
		--vis-hide f00000033 \
		--vis-node-conf f00000034 below.href '{{ f00000034 }}' \
		--vis-node-conf f00000034 below.label '4. Building? No.' \
		--vis-node-conf f00000035 below.href '{{ f00000035 }}' \
		--vis-node-conf f00000035 below.label '3. Landscape? Yes.' \
		--vis-node-conf f00000036 below.href '{{ f00000036 }}' \
		--vis-node-conf f00000036 below.label '2. Road? No.' \
		--vis-node-conf f00000036 left.href '{{ original }}' \
		--vis-node-conf f00000036 left.label '1. Start here' \
		--vis-node-conf f00000036 left.sublabel 'Goal: Classify center pixel' \
		--vis-zoom 1.75 \
		--vis-color-path-to vegetation \
		--vis-below-dy 250 \
		--vis-scale 0.8 \
		--vis-margin-top -100 \
		--vis-height 400 \
		--vis-width 800
```

```
nbdt-hierarchy \
		--path graph-induced-hrnet_w18_small_v1_cityscapes_cls19_1024x2048_trainset.json \
		--vis-no-color-leaves \
		--vis-out-fname template \
		--vis-root f00000031 \
		--vis-hide f00000029 n04576211 \
		--vis-node-conf n00003553 below.dy 250 \
		--vis-node-conf n00003553 below.href '{{ n00003553 }}' \
		--vis-node-conf n00003553 below.label '4. Rider? Yes.' \
		--vis-node-conf n00002684 below.dy 350 \
		--vis-node-conf n00002684 below.href '{{ n00002684 }}' \
		--vis-node-conf n00002684 below.label '3. Cyclist? Yes.' \
		--vis-node-conf f00000031 below.dy 250 \
		--vis-node-conf f00000031 below.href '{{ f00000031 }}' \
		--vis-node-conf f00000031 below.label '2. People? Yes.' \
		--vis-node-conf f00000031 left.href '{{ original }}' \
		--vis-node-conf f00000031 left.label '1. Start here' \
		--vis-node-conf f00000031 left.sublabel 'Goal: Classify center pixel' \
		--vis-zoom 1.75 \
		--vis-color-path-to rider \
		--vis-below-dy 375 \
		--vis-scale 0.8 \
		--vis-margin-top -75 \
		--vis-height 400 \
		--vis-width 900
```

```
nbdt-hierarchy \
		--path graph-induced-hrnet_w18_small_v1_cityscapes_cls19_1024x2048_trainset.json \
		--vis-no-color-leaves \
		--vis-out-fname template \
		--vis-root f00000033 \
		--vis-hide f00000032 f00000034 \
		--vis-node-conf n04341686 below.dy 200 \
		--vis-node-conf n04341686 below.href '{{ n04341686 }}' \
		--vis-node-conf n04341686 below.label '5. Wall? Yes.' \
		--vis-node-conf n00001930 below.dy 250 \
		--vis-node-conf n00001930 below.href '{{ n00001930 }}' \
		--vis-node-conf n00001930 below.label '4. Structure? Yes.' \
		--vis-node-conf f00000030 below.dy 350 \
		--vis-node-conf f00000030 below.href '{{ f00000030 }}' \
		--vis-node-conf f00000030 below.label '3. Verge? No.' \
		--vis-node-conf f00000033 below.href '{{ f00000033 }}' \
		--vis-node-conf f00000033 below.label '2. Pavement? No.' \
		--vis-node-conf f00000033 left.href '{{ original }}' \
		--vis-node-conf f00000033 left.label '1. Start here' \
		--vis-node-conf f00000033 left.sublabel 'Goal: Classify center pixel' \
		--vis-zoom 1.75 \
		--vis-color-path-to wall \
		--vis-below-dy 250 \
		--vis-scale 0.8 \
		--vis-margin-top -75 \
		--vis-height 400 \
		--vis-width 900
```

```
nbdt-hierarchy \
		--path graph-induced-hrnet_w18_small_v1_cityscapes_cls19_1024x2048_trainset.json \
		--vis-no-color-leaves \
		--vis-out-fname template \
		--vis-root f00000031 \
		--vis-hide f00000029 \
		--vis-node-conf n04576211 below.dy 200 \
		--vis-node-conf n04576211 below.href '{{ n04576211 }}' \
		--vis-node-conf n04576211 below.label '5. Bicycle? Yes.' \
		--vis-node-conf n00003553 below.dy 250 \
		--vis-node-conf n00003553 below.href '{{ n00003553 }}' \
		--vis-node-conf n00003553 below.label '4. Rider? No.' \
		--vis-node-conf n00002684 below.dy 350 \
		--vis-node-conf n00002684 below.href '{{ n00002684 }}' \
		--vis-node-conf n00002684 below.label '3. Cyclist? Yes.' \
		--vis-node-conf f00000031 below.dy 250 \
		--vis-node-conf f00000031 below.href '{{ f00000031 }}' \
		--vis-node-conf f00000031 below.label '2. People? Yes.' \
		--vis-node-conf f00000031 left.href '{{ original }}' \
		--vis-node-conf f00000031 left.label '1. Start here' \
		--vis-node-conf f00000031 left.sublabel 'Goal: Classify center pixel' \
		--vis-zoom 1.75 \
		--vis-color-path-to bicycle \
		--vis-below-dy 375 \
		--vis-scale 0.8 \
		--vis-margin-top -75 \
		--vis-height 400 \
		--vis-width 900
```

```
nbdt-hierarchy \
		--path graph-induced-hrnet_w18_small_v1_cityscapes_cls19_1024x2048_trainset.json \
		--vis-no-color-leaves \
		--vis-out-fname template \
    --vis-root f00000031 \
		--vis-hide n03100490 n00002684 n00033020 n00001740 \
		--vis-node-conf f00000031 below.href '{{ f00000031 }}' \
		--vis-node-conf f00000031 below.label '2. Person or bike? No.' \
		--vis-node-conf f00000031 below.sublabel 'Looks for person, wheel' \
		--vis-node-conf f00000031 below.dy 250 \
		--vis-node-conf f00000029 below.href '{{ f00000029 }}' \
		--vis-node-conf f00000029 below.label '3. Pole-like? Yes.' \
		--vis-node-conf f00000029 below.dy 225 \
		--vis-node-conf f00000028 below.href '{{ f00000028 }}' \
		--vis-node-conf f00000028 below.label '4. Sky? Yes.' \
		--vis-node-conf f00000031 left.href '{{ original }}' \
		--vis-node-conf f00000031 left.label '1. Start here' \
		--vis-node-conf f00000031 left.sublabel 'Goal: Classify center pixel' \
		--vis-zoom 1.75 \
		--vis-color-path-to sky \
		--vis-below-dy 200 \
		--vis-scale 0.8 \
		--vis-margin-top -62 \
		--vis-height 325 \
		--vis-width 900
```

```
nbdt-hierarchy \
		--path graph-induced-hrnet_w18_small_v1_cityscapes_cls19_1024x2048_trainset.json \
		--vis-no-color-leaves \
		--vis-out-fname template \
    --vis-root f00000029 \
		--vis-hide n03100490 n00002684 \
		--vis-node-conf f00000029 below.href '{{ f00000029 }}' \
		--vis-node-conf f00000029 below.label '3. Pole-like? Yes.' \
		--vis-node-conf f00000029 below.dy 225 \
		--vis-node-conf f00000028 below.href '{{ f00000028 }}' \
		--vis-node-conf f00000028 below.label '4. Sky? No.' \
		--vis-node-conf n00001740 below.href '{{ n00001740 }}' \
		--vis-node-conf n00001740 below.label '5. Pole? No.' \
		--vis-node-conf n00033020 below.href '{{ n00033020 }}' \
		--vis-node-conf n00033020 below.label '6. Traffic Light? Yes.' \
		--vis-node-conf f00000029 left.href '{{ original }}' \
		--vis-node-conf f00000029 left.label '1. Start here' \
		--vis-node-conf f00000029 left.sublabel 'Goal: Classify center pixel' \
		--vis-zoom 1.75 \
		--vis-color-path-to traffic_light \
		--vis-below-dy 200 \
		--vis-scale 0.8 \
		--vis-margin-top -50 \
		--vis-height 350 \
		--vis-width 900
```

</details>

<details>
	<summary>3. Generate all figures</summary>

```
for cls in car building vegetation bus sidewalk rider wall bicycle sky traffic_light; do python tools/vis_copy.py template-${cls}.html --dirs-for-cls ${cls} --suffix=-${cls}; done
```
</details>

<details>
	<summary>Optionally generate survey</summary>

```
python tools/vis_survey.py --baseline `ls SegGradCAM*crop400/*` --baseline-original `ls SegGradCAM*original/*` --ours image*.html
```

</details>

## Fine-Grained Visual Decision Rules: Semantic Input Removal (SIR)

We run SIR on ADE20K to analyze the impact of various car parts on accuracy. Note that this analysis requires the full ADE20K dataset, while the ADE20K training setup above only uses the scene parsing subset of ADE20K. The full dataset can be downloaded [here](https://groups.csail.mit.edu/vision/datasets/ADE20K/); alternatively, run the following:
```
wget http://groups.csail.mit.edu/vision/datasets/ADE20K/ADE20K_2016_07_26.zip 
unzip ADE20K_2016_07_26.zip 
```
Place the dataset in the `data` directory under `ade20k_full`, i.e. the full path will be `SegNBDT/data/ade20k_full`.

To run the script, specify the path to the pretrained model using the `TEST.MODEL_FILE` parameter and run
```
python ade20k_car_part_analysis.py —cfg ${CONFIG} —index ${INDEX} —wnid ${WNID} TEST.MODEL_FILE ${CHECKPOINT}
```
- `cfg`: ADE20K scene parsing configuration file (e.g. `experiments/ade20k/nbdt/*.yml`)
- `wnid`: wnid of node to run analysis on 
- `index`: index of the input ADE20K image (0-indexed)

Consider the following example:
```
python tools/ade20k_car_part_analysis.py \
    --cfg experiments/ade20k/nbdt/seg_hrnet_w48_520x520_sgd_lr2e-2_wd1e-4_bs_16_epoch120_tsw10.yaml \
    --index 2038 \
    --wnid f00000255 \
    TEST.MODEL_FILE output/ade20k/seg_hrnet_w48_520x520_sgd_lr2e-2_wd1e-4_bs_16_epoch120_tsw10/best.pth
```
![car_part_analysis](https://user-images.githubusercontent.com/11863465/84226818-a730d380-aa97-11ea-944d-0a3ad8663a1b.png)

# Results

All models use the HRNetV2-W48 architecture initialized by weights pretrained on ImageNet. Note that: LIP is evaluated with flip, Pascal-Context is evaluated with multi-scale (0.5,0.75,1.0,1.25,1.5,1.75) and flip.

|                      | Cityscapes | Pascal-Context | LIP    | ADE20K |
|----------------------|------------|----------------|--------|--------|
| NN Baseline          | 81.12%     | 52.54%         | 55.37% | 42.58% |
| NBDT-S (Ours)        | 79.01%     | 49.12%         | 51.64% | 35.83% |
| Performance Gap      | 2.11%      | 3.42%          | 3.73%  |  6.75% |

# Citation

If you find this work useful for your research, please cite our [paper](https://arxiv.org/abs/2006.06868):

```
@misc{wan2020segnbdt,
    title={SegNBDT: Visual Decision Rules for Segmentation},
    author={Alvin Wan and Daniel Ho and Younjin Song and Henk Tillman and Sarah Adel Bargal and Joseph E. Gonzalez},
    year={2020},
    eprint={2006.06868},
    archivePrefix={arXiv},
    primaryClass={cs.CV}
}
```
