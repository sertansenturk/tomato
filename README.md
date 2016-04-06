[![Build Status](https://travis-ci.org/sertansenturk/ahenkidentifier.svg?branch=master)](https://travis-ci.org/sertansenturk/ahenkidentifier) [![GitHub version](https://badge.fury.io/gh/sertansenturk%2Ftomato.svg)](https://badge.fury.io/gh/sertansenturk%2Ftomato) [![Code Climate](https://codeclimate.com/github/sertansenturk/tomato/badges/gpa.svg)](https://codeclimate.com/github/sertansenturk/tomato)

# tomato
**T**urkish-**O**ttoman **M**akam (M)usic **A**nalysis **TO**olbox

Introduction
------
**tomato** is a comprehensive and easy-to-use toolbox for the analysis of audio recordings and music scores of Turkish-Ottoman makam music. The toolbox includes the state of art methodologies applied on this music tradition. The analysis tasks include:

- **Audio Analysis:** predominant melody extraction, tonic and transposition identification, histogram analysis, tuning analysis, (makam recognition is coming soon)
- **Symbolic Analysis:** score metadata extraction, score section extraction, score phrase segmentation, semiotic section and phrase analysis
- **Joint Analysis:** score-informed tonic identification and tempo estimation, section linking, note-level audio-score alignment, predominant melody octave correction, note models, (usul tracking is coming soon)

The aim of the toolbox is to allow the user to easily analyze large-scale audio recording and music score collections of Turkish-Ottoman makam music, using the state of the art methodologies specifically designed for the culture-specific characteristics of this tradition. The analysis results can then be further used for several tasks such as automatic content description, music discovery/recommendation and musicological analysis.

For the methodologies and their implementations in the toolbox, please refer to the [References](#references).

Documentation
------
Coming soon...

License
------
Coming soon...

Installation
-------

There are three steps in installation:

1. [Installing tomato](#tomato_install)
2. [Installing Essentia](#essentia_install)
3. [Installing MATLAB Runtime](#mcr_install)

#### <a name="tomato_install"></a>Installing tomato
If you want to install **tomato**, it is recommended to install the package and dependencies into a virtualenv. In the terminal, do the following:

    virtualenv env
    source env/bin/activate
    
Then change the current directory to the repository folder and install by:

    cd path/to/tomato
    python setup.py install
    
The requirements are installed during the setup. If that step does not work for some reason, you can install the requirements by calling:

    pip install -r requirements

If you want to edit files in the package and want the changes reflected, you should call:

    cd path/to/tomato
    pip install -e .

#### <a name="essentia_install"></a>Installing Essentia

__tomato__ uses several modules in Essentia. Follow the [instructions](essentia.upf.edu/documentation/installing.html) to install the library. Then you should link the python bindings of Essentia in the virtual environment:

    ln -s path_to_essentia_bindings path_to_env/lib/python2.7/site-packages
    
Don't forget to change the `path_to_essentia_bindings` and `path_to_env` with the actual path of the installed Essentia Python bindings and the path of your virtualenv, respectively. Depending on the Essentia version, the default installation path of the Essentia bindings is either `/usr/local/lib/python2.7/dist-packages/essentia` or `/usr/local/lib/python2.7/site-packages/essentia`.

#### <a name="mcr_install"></a>Installing MATLAB Runtime

The score phrase segmentation, score-informed joint tonic identification and tempo estimation, section linking and note-level audio-score alignment algorithms are implemented in MATLAB and compiled as binaries. They need **MATLAB Runtime for R2015a (8.5)** to run. You should download and install this specific version  (links for [Linux](http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip) and [Mac OSX](http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/maci64/MCR_R2015a_maci64_installer.zip)). 

We recommend you to install MATLAB Runtime in the default installation path, as **tomato** searches them automatically. Otherwise, you have to specify your own path in the MATLAB Runtime configuration file, [tomato/config/mcr_path.cfg](https://github.com/sertansenturk/tomato/blob/master/tomato/config/mcr_path.cfg).

Basic Usage
-------

```python
from tomato.audio.AudioAnalyzer import AudioAnalyzer
from tomato.symbolic.SymbTrAnalyzer import SymbTrAnalyzer
from tomato.joint.JointAnalyzer import JointAnalyzer

# score filepaths
symbtr_name = 'makam--form--usul--name--composer'
txt_score_filepath = 'path/to/txt_score'
mu2_score_filepath = 'path/to/mu2_score'

# audio filepath
audio_filepath = 'path/to/audio'

# instantiate analyzer objects
scoreAnalyzer = SymbTrAnalyzer(verbose=True)
audioAnalyzer = AudioAnalyzer(verbose=True)
jointAnalyzer = JointAnalyzer(verbose=True)

# score analysis
score_features = scoreAnalyzer.analyze(
    txt_score_filepath, mu2_score_filepath, symbtr_name=symbtr_name)

# audio analysis
audio_features = audioAnalyzer.analyze(
    audio_filepath, makam=score_features['makam']['symbtr_slug'])

# joint analysis
joint_features, score_informed_audio_features = jointAnalyzer.analyze(
    txt_score_filepath, score_features, audio_filepath, audio_features['pitch'])

# redo some steps in audio analysis
score_informed_audio_features = audioAnalyzer.update_analysis(
    score_informed_audio_features)

# summarize all the features extracted from all sources
summarized_features = jointAnalyzer.summarize(
    audio_features, score_features, joint_features, score_informed_audio_features)
```

You can refer to [audio_analysis_demo.ipynb](https://github.com/sertansenturk/tomato/blob/master/audio_analysis_demo.ipynb), [score_analysis_demo.ipynb](https://github.com/sertansenturk/tomato/blob/master/score_analysis_demo.ipynb), [joint_analysis_demo.ipynb](https://github.com/sertansenturk/tomato/blob/master/joint_analysis_demo.ipynb) and [complete_analysis_demo.ipynb](https://github.com/sertansenturk/tomato/blob/master/complete_analysis_demo.ipynb) for interactive demos.

FAQ
-------
1. **Which operating systems are suppported?**

    The algorithms, which are written purely in Python, are platform independent. However [compiling Essentia in Windows](http://essentia.upf.edu/documentation/installing.html#building-essentia-on-windows) is not straightforward yet. Therefore we have only compiled the MATLAB binaries for **Mac OSX** and **Linux**.
    If you have compiled Essentia for Windows somehow or if you have any OS specific problems, please submit an [issue](https://github.com/sertansenturk/tomato/issues).

2. **What are the supported Python versions?**

    Currently we only support 2.7. We will start working on Python 3+ support, as soon as [Essentia bindings for Python 3](https://github.com/MTG/essentia/issues/138) are available.

3. **Where are the MATLAB binaries?**

    The binaries are not stored in **tomato**, because they relatively big. It would take too much space to store them here, including the versions introduced in each modification. Instead the binaries are provided within the releases of the relevant packages. The binaries are downloaded to [tomato/bin](https://github.com/sertansenturk/tomato/blob/master/tomato/bin) during the installation process of tomato.
    Please refer to [tomato/config/bin.cfg](https://github.com/sertansenturk/tomato/blob/master/tomato/config/bin.cfg) for the relevant releases.

Authors
-------
Sertan Şentürk
contact@sertansenturk.com

<a name="references"></a>References
-------
Thesis
