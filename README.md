# tomato
**T**urkish-**O**ttoman **M**akam (M)usic **A**nalysis **TO**olbox

Introduction
------
**tomato** is a comprehensive and easy-to-use toolbox for the analysis of audio recordings and music scores of Turkish-Ottoman makam music.  The toolbox showcases the state of art methodologies applied on this music tradition. The analysis tasks include:

- **Audio Analysis:** predominant melody extraction, tonic and transposition identification, histogram analysis, tuning analysis, (makam recognition is coming soon)
- **Symbolic Analysis:** (coming soon) score metadata extraction, score section extraction, score phase segmentation, semiotic section and phrase analysis
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

Authors
-------
Sertan Şentürk
contact@sertansenturk.com

Reference
-------
Thesis
