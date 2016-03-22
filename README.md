# tomato
**T**urkish-**O**ttoman **M**akam (M)usic **A**nalysis **TO**olbox

Introduction
------
**tomato** is a comprehensive and easy-to-use toolbox for the analysis of audio recordings and music scores of Turkish-Ottoman makam music. The toolbox includes the state of art methodologies applied on this music tradition. The analysis tasks include:

- **Audio Analysis:** predominant melody extraction, tonic and transposition identification, histogram analysis, tuning analysis, (makam recognition is coming soon)
- **Symbolic Analysis:** (coming soon) score metadata extraction, score section extraction, score phrase segmentation, semiotic section and phrase analysis
- **Score-Informed Audio Analysis:** (coming soon) partial audio-score alignment, joint tonic identification and tempo estimation, section linking, note-level audio-score alignment, predominant melody octave correction, note models, usul tracking

The aim of the toolbox is to allow the user to easily analyze large-scale audio recording and music score collections of Turkish-Ottoman makam music, using the state of the art methodologies specifically designed for the necessities of this tradition. The analysis results can then be further used for several tasks such as automatic content description, music discovery/recommendation and musicological analysis.

For the methodologies and their implementations in the toolbox, please refer to the References (coming soon).

Documentation
------
Coming soon...

Installation
-------

If you want to install **tomato**, it is recommended to install the package and dependencies into a virtualenv. In the terminal, do the following:

    virtualenv env
    source env/bin/activate
    
Then change the current directory to the repository folder and install by:

    cd path/to/tomato
    python setup.py install

If you want to be able to edit files and have the changes be reflected, then install the repository like this instead:

    cd path/to/tomato
    pip install -e .

The algorithm uses several modules in Essentia. Follow the [instructions](essentia.upf.edu/documentation/installing.html) to install the library. Then you should link the python bindings of Essentia in the virtual environment:

    ln -s /usr/local/lib/python2.7/dist-packages/essentia env/lib/python2.7/site-packages

Now you can install the rest of the dependencies:

    pip install -r requirements
    
The score phrase segmentation, score-informed joint tonic identification and tempo estimation, section linking and note-level audio-score alignment algorithms are implemented in MATLAB and compiled as binaries. They need **MATLAB Runtime Compiler for R2015a (8.5)** to run. You should download (links for [Linux](http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip) and [Max OSX](http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/maci64/MCR_R2015a_maci64_installer.zip)) and install this specific version. We recommend you to install MCR in the default installation path as **tomato** searches the default path automatically. Otherwise you have to specify your own path in the MCR configuration file.

Basic Usage
-------

Below you can find some basic calls:

##### Audio Analysis
```python
from tomato.audio.AudioAnalyzer import AudioAnalyzer

audio_filepath = 'path/to/audio'
makam = 'makam_name'  # the makam slug. See the documentation for possible values

audioAnalyzer = AudioAnalyzer()
features = audioAnalyzer.analyze(audio_filepath, makam=makam)

# plot the features
import pylab
audioAnalyzer.plot(features)
pylab.show()

# save features to a json file
audioAnalyzer.save_features(features, 'save_filename.json')
```

You can refer to [audio_analysis_demo.ipynb](https://github.com/sertansenturk/tomato/blob/master/audio_analysis_demo.ipynb) for an interactive demo.

##### Symbolic Analysis
Coming soon...

##### Score-Informed Audio Analysis
Coming soon...

FAQ
-------
1. **Which operating systems are suppported?**

    The algorithms, which are written purely in Python are platform independent. However [compiling Essentia in Windows](http://essentia.upf.edu/documentation/installing.html#building-essentia-on-windows) is not straightforward yet. Therefore we have only compiled the MATLAB binaries for **Mac OSX** and **Linux**.
    If you have compiled Essentia for Windows somehow or if you have any OS specific problems, please submit an [issue](https://github.com/sertansenturk/tomato/issues) for requests.

2. **What are the supported Python versions?**

    Currently we only support 2.7. We will start working on Python 3+ support, as soon as Essentia bindings for Python 3+ are available.

3. **Where are the MATLAB binaries?**

    The binaries are not stored in **tomato**, because they relatively big and it would take too much space to store them in the repository including the versions introduced in each modification. Instead the binaries are hosted in [tomato_binaries](https://github.com/sertansenturk/tomato_binaries). The binaries are downloaded from this repository during the installation process of tomato.

Authors
-------
Sertan Şentürk
contact@sertansenturk.com

Reference
-------
Thesis
