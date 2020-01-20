# tomato

**T**urkish-**O**ttoman **M**akam (M)usic **A**nalysis **TO**olbox

[![Build Status](https://travis-ci.com/sertansenturk/tomato.svg?branch=master)](https://travis-ci.com/sertansenturk/tomato) [![GitHub version](https://badge.fury.io/gh/sertansenturk%2Ftomato.svg)](https://badge.fury.io/gh/sertansenturk%2Ftomato) [![Code Climate](https://codeclimate.com/github/sertansenturk/tomato/badges/gpa.svg)](https://codeclimate.com/github/sertansenturk/tomato) [![DOI](https://zenodo.org/badge/21104/sertansenturk/tomato.svg)](https://zenodo.org/badge/latestdoi/21104/sertansenturk/tomato) [![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-ff69b4.svg)](http://www.gnu.org/licenses/agpl-3.0) [![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-ff69b4.svg)](http://creativecommons.org/licenses/by-nc-sa/4.0/)

## Table of contents

- [1. Introduction](#1-introduction)
- [2. tomato in a nutshell](#2-tomato-in-a-nutshell)
- [3. Installation](#3-installation)
  - [3.1. Prequisites](#31-prequisites)
  - [3.2. Install tomato using make](#32-install-tomato-using-gnu-make)
  - [3.3. Running tomato using docker](#33-running-tomato-using-docker)
  - [3.4. Step-by-step installation](#34-step-by-step-installation)
    - [3.4.1. Installing tomato](#341-installing-tomato)
    - [3.4.2. Installing MATLAB runtime](#342-installing-matlab-runtime)
    - [3.4.3. Installing LilyPond](343-installing-lilypond)
- [4. Documentation](#4-documentation)
- [5. License](#5-license)
- [6. FAQ](#6-faq)
- [7. Authors](7-authors)
- [8. Acknowledgments](#8-acknowledgments)
- [9. References](#9-references)

## 1. Introduction

`tomato` is a comprehensive and easy-to-use toolbox in Python for the analysis of audio recordings and music scores of Turkish-Ottoman makam music. The toolbox includes the state of art methodologies applied to this music tradition. The analysis tasks include:

- **Symbolic Analysis:** score metadata extraction, score section extraction, score phrase segmentation, semiotic section, and phrase analysis
- **Audio Analysis:** audio metadata crawling, predominant melody extraction, tonic and transposition identification, makam recognition, pitch distribution computation, tuning analysis, melodic progression analysis
- **Joint Analysis:** score-informed tonic identification and tempo estimation, section linking, note-level audio-score alignment, predominant melody octave correction, note modeling

The toolbox aims to facilitate the analysis of large-scale audio recording and music score collections of Turkish-Ottoman makam music, using the state of the art methodologies designed for the culture-specific characteristics of this tradition. The analysis results can then be further used for several tasks such as automatic content description, music discovery/recommendation, and musicological analysis.

If you are using `tomato` in your work, please cite the dissertation:

> Şentürk, S. (2016). [Computational Analysis of Audio Recordings and Music Scores for the Description and Discovery of Ottoman-Turkish Makam Music](http://sertansenturk.com/research/works/phd-thesis/). Ph.D. thesis, Universitat Pompeu Fabra, Barcelona, Spain.

For the sake of __reproducibility__, please also state the version you used as indexed at [Zenodo](https://zenodo.org/search?page=1&size=20&q=conceptrecid:%22597862%22&sort=-version&all_versions=True).

For the descriptions of the methodologies in the toolbox, please refer to the papers listed in the [References](#references).

## 2. tomato in a nutshell

```python
# import ...
from tomato.joint.completeanalyzer import CompleteAnalyzer
from matplotlib import pyplot as plt

# score input
symbtr_name = 'makam--form--usul--name--composer'
txt_score_filename = 'path/to/txt_score'
mu2_score_filename = 'path/to/mu2_score'

# audio input
audio_filename = 'path/to/audio'
audio_mbid = '11111111-1111-1111-1111-11111111111'  # MusicBrainz Recording Identifier

# instantiate analyzer object
completeAnalyzer = CompleteAnalyzer()

# Apply the complete analysis. The resulting tuple will have
# (summarized_features, score_features, audio_features,
# score_informed_audio_features, joint_features) in order
results = completeAnalyzer.analyze(
    symbtr_name=symbtr_name, symbtr_txt_filename=txt_score_filepath,
    symbtr_mu2_filename=mu2_score_filepath, audio_filename=audio_filepath,
    audio_metadata=audio_mbid)

# plot the summarized features
fig, ax = completeAnalyzer.plot(results[0])
ax[0].set_ylim([50, 500])
plt.show()
```

You can refer to the Jupyter notebooks in [demos](https://github.com/sertansenturk/tomato/blob/master/demos) folder for detailed, interactive examples.

## 3. Installation

### 3.1. Prequisites

`tomato` may require several packages to be installed, depending on your operating system. For example, in *Ubuntu 16.04* using *Python 3.5*, you have to install the _python 3_, _libxml2, libxslt1, freetype_, and _png_ development packages. You can install them by:

```bash
sudo apt-get install python3 python3.5-dev python3-pip libxml2-dev libxslt1-dev libfreetype6-dev libpng12-dev
```

### 3.2. Install tomato using GNU make

You can install `tomato` and all its dependencies by running:

```bash
make
```

The above command installs `tomato` to a virtual environment called `./venv`.

If you want to install `tomato` in editable mode and with the extra Python requirements (namely `demo` and `development` requirements), you can call:

```bash
make all-editable
```

### 3.3. Running tomato using docker

For the reproducibility and maintability's sake, `tomato` also comes with `docker` support.

To build the docker image simply go to the base folder of the repository and run:

```bash
docker build . -t sertansenturk/tomato:latest
```

You may interact with the docker image in many different ways. Below, we run a container by mounting the `demos` folder in tomato and start an interactive `bash` session:

```bash
docker run -v "$PWD/demos/":/home/tomato_user/demos/ -it sertansenturk/tomato bash
```

Then, you can work on the command line, like you are on your local machine. Any changes you make to the `demos` folder will be reflected back to your local folder.

For more information on working with `docker`, please refer to the [official documentation](https://docs.docker.com/get-started/).

### 3.4. Step-by-step installation

If the above options do not work for you, you need to complete the three steps below:

#### 3.4.1. Installing tomato

It is recommended to install `tomato` and its dependencies into a virtualenv. In the terminal, do the following:

```bash
virtualenv -p python3 venv
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Then, change the current directory to the repository folder and install by:

```bash
cd path/to/tomato
python -m pip install .
```

If you want to edit files in the package and have the changes reflected, instead, you can call:

```bash
python -m pip install -e .
```

If you want to run the demo Jupyter notebooks and/or make development, you may include the extras to the installation by:

```bash
python -m pip install -e .[demo,development]
```

The requirements are installed during the setup. If that step does not work for some reason, you can install the requirements by calling:

```bash
pip install -r requirements.txt
```

#### 3.4.2. Installing MATLAB runtime

The score phrase segmentation, score-informed joint tonic identification and tempo estimation, section linking, and note-level audio-score alignment algorithms are implemented in MATLAB and compiled as binaries. They need **MATLAB Runtime for R2015a (8.5)** to run. You must download and install this specific version ([Linux installer](http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip)).

We recommend you to install MATLAB Runtime in the default installation path, as `tomato` searches them automatically. Otherwise, you have to specify your own path in the MATLAB Runtime configuration file, [tomato/config/mcr_path.cfg](https://github.com/sertansenturk/tomato/blob/master/tomato/config/mcr_path.cfg).

#### 3.4.3. Installing LilyPond

`tomato` uses LilyPond under the hood to convert the music scores to SVG format.

In most Linux distributions, you can install LilyPond from the software repository of your distribution (e.g., `sudo apt install lilypond` in Debian-based distributions).

`tomato` requires *LilyPond* version 2.18.2 or above. If your distribution comes with an older version, we recommend you to download the latest stable version from the [LilyPond website](http://lilypond.org/download.html). If you had to install LilyPond this way, you might need to enter the LilyPond binary path to the "custom" field in [tomato/config/lilypond.cfg](https://github.com/sertansenturk/tomato/tree/master/tomato/config) (the default location is ```$HOME/bin/lilypond```).

## 4. Documentation

Coming soon...

## 5. License

The source code hosted in this repository is licensed under [Affero GPL version 3](https://www.gnu.org/licenses/agpl-3.0.en.html).

Any data (the music scores, extracted features, training models, figures, outputs, etc.) are licensed under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).

## 6. FAQ

1. **The notes aligned by `JointAnalyzer.align_audio_score(...)` seems shifted. What is the problem?**

    Your audio input is probably a compressed format, such as *mp3*. There are typically shifts between different decoders (and even different versions of the same decoder) when they decode the same compressed audio file. In the predominant melody extraction step (`AudioAnalyzer.extract_pitch(...)`), Essentia has to decode the recording for processing. You observe a shift when the application you use another decoder.

    These shifts are typically small (e.g., 50 samples ~1ms), so they are not very problematic. Nevertheless, there is no guarantee that the shift will be prominent. If you need "perfect" synchronization, you should use an uncompressed format such as *wav* as the audio input.

    **Note:** In demos, we use *mp3*, because it would be too bulky to host a *wav* file.

2. **Which operating systems are supported?**

    - `tomato` is fully supported **only in Linux**. It is tested against *Ubuntu 16.04* and *18.04*.
    - We suggest people use the [tomato docker image](#running-tomato-using-docker) for other operating systems.
    - `tomato` was tested on *Mac OSX Sierra* until version [v0.10.1](https://github.com/sertansenturk/tomato/releases/tag/v0.10.1). You can still install `tomato` on *Mac OSX* by referring to the [Linux installation instructions](#installation), but you need to install and configure [Essentia](https://essentia.upf.edu/installing.html#mac-osx) & [MATLAB Compiler Runtime](https://ssd.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/maci64/MCR_R2015a_maci64_installer.zip) by yourself.

3. **What are the supported Python versions?**

    `tomato` supports Python versions 3.5, 3.6, and 3.7. If you want to run `tomato` on Python 2.7, please install [v0.13.0](https://github.com/sertansenturk/tomato/releases/tag/v0.13.0) or below.

4. **Where are the MATLAB binaries?**

    The binaries are not stored in `tomato` because they are relatively big. It would take too much space to store them here, including the versions introduced in each modification. Instead, the binaries are provided within the releases of the relevant packages. The binaries are downloaded to [tomato/bin](https://github.com/sertansenturk/tomato/blob/master/tomato/bin) during the installation.

    Please refer to [tomato/config/bin.cfg](https://github.com/sertansenturk/tomato/blob/master/tomato/config/bin.cfg) for the relevant releases.

5. **`ScoreConverter` fails to convert music scores with an error saying "The LilyPond path is not found." How can I fix this problem?**

    There can be several reasons regarding this problem:

    - The user-provided file path (the music score input) does not exist.

        Check your input MusicXML-score path.

    - LilyPond is not installed.

        Install the appropriate version of LilyPondby following [the instructions](#installing-lilypond).

    - The binary path exists, but it is not used.

        Add the path of the LilyPond binary to the "custom" section in the configuration file: `./tomato/config/lilypond.cfg`.

6. Is `tomato` a fruit or a vegetable?

    It has a culture-specific answer.

## 7. Authors

Sertan Şentürk
contact@sertansenturk.com

## 8. Acknowledgments

We would like to thank [Harold Hagopian](https://en.wikipedia.org/wiki/Harold_Hagopian), the founder of [Traditional Crossroads](http://traditionalcrossroads.com/About-Us), for allowing us to use Tanburi Cemil Bey's performance of [Uşşak Sazsemaisi](http://musicbrainz.org/recording/f970f1e0-0be9-4914-8302-709a0eac088e) in our demos.

## 9. References

_The toolbox has been realized as part of the thesis:_

**[1]** Şentürk, S. (2016). *Computational analysis of audio recordings and music scores for the description and discovery of Ottoman-Turkish makam music.* Ph.D. thesis, Universitat Pompeu Fabra, Barcelona, Spain.  

_The methods used in the toolbox are described in the papers:_

__Score Phrase Segmentation__  
**[2]** Bozkurt, B., Karaosmanoğlu, M. K., Karaçalı, B., and Ünal, E. (2014). *Usul and makam driven automatic melodic segmentation for Turkish music.* Journal of New Music Research. 43(4):375–389.

__Score Section Extraction; Semiotic Section and Phrase Analysis__  
**[3]** Şentürk S., and Serra X. (2016). *A method for structural analysis of Ottoman-Turkish makam music scores.* In Proceedings of 6th International Workshop on Folk Music Analysis (FMA 2016), pages 39–46, Dublin, Ireland.

__Audio Predominant Melody Extraction__  
**[4]** Atlı, H. S., Uyar, B., Şentürk, S., Bozkurt, B., and Serra, X. (2014). *Audio feature extraction for exploring Turkish makam music.* In Proceedings of 3rd International Conference on Audio Technologies for Music and Media (ATMM 2014), pages 142–153, Ankara, Turkey.

__Audio Pitch Filter__  
**[5]** Bozkurt, B. (2008). *An automatic pitch analysis method for Turkish maqam music.* Journal of New Music Research. 37(1):1–13.

__Audio Tonic and Transposition Identification, Makam Recognition, Pitch Distribution Computation, Tuning Analysis__  
**[6]** Bozkurt, B. (2008). *An automatic pitch analysis method for Turkish maqam music.* Journal of New Music Research. 37(1):1–13.  
**[7]** Gedik, A. C., and Bozkurt, B. (2010). *Pitch-frequency histogram-based music information retrieval for Turkish music.* Signal Processing. 90(4):1049–1063.  
**[8]** Chordia, P., and Şentürk, S. (2013). *Joint recognition of raag and tonic in North Indian music.* Computer Music Journal. 37(3):82–98.  

__Audio Tonic Identification from the Last Note__  
**[9]** Atlı, H. S., Bozkurt, B., and Şentürk, S. (2015). *A method for tonic frequency identification of Turkish makam music recordings.* In Proceedings of 5th International Workshop on Folk Music Analysis (FMA 2015), pages 119–122, Paris, France.

__Audio Melodic Progression (Seyir) Analysis__  
**[10]** Bozkurt B. (2015). *Computational analysis of overall melodic progression for Turkish Makam Music.* In Penser l’improvisation, pages 289–298, Delatour France, Sampzon.

__Score-Informed Audio Tonic Identification__  
**[11]** Şentürk, S., Gulati, S., and Serra, X. (2013). *Score informed tonic identification for makam music of Turkey.* In Proceedings of 14th International Society for Music Information Retrieval Conference (ISMIR 2013), pages 175–180, Curitiba, Brazil.

__Score-Informed Audio Tempo Estimation__  
**[12]** Holzapfel, A., Şimşekli U., Şentürk S., and Cemgil A. T. (2015). *Section-level modeling of musical audio for linking performances to scores in Turkish makam music.* In Proceedings of 40th IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP 2015), pages 141–145, Brisbane, Australia.

__Audio-Score Section Linking__  
**[13]** Şentürk, S., Holzapfel, A., and Serra, X. (2014). *Linking scores and audio recordings in makam music of Turkey.* Journal of New Music Research, 43(1):34–52.

__Note-Level Audio-Score Aligment__  
**[14]** Şentürk, S., Gulati, S., and Serra, X. (2014). *Towards alignment of score and audio recordings of Ottoman-Turkish makam music.* In Proceedings of 4th International Workshop on Folk Music Analysis (FMA 2014), pages 57–60, Istanbul, Turkey.

__Score-Informed Audio Predominant Melody Correction; Note Modeling__  
**[15]** Şentürk, S., Koduri G. K., and Serra X. (2016). *A score-informed computational description of svaras using a statistical model.* In Proceedings of 13th Sound and Music Computing Conference (SMC 2016), pages 427–433, Hamburg, Germany.
