#### tomato v0.7.0dev
 - Improved code quality
 - All note indices in the outputs are fixed to **1-indexing** according to
 the Symbtr-txt convention (not the pythonic 0-indexing)
 - Updated requirements

#### tomato v0.6.0
 - Added audio metadata fetching from MusicBrainz using [makammusicbrainz](https://github.com/sertansenturk/makammusicbrainz/releases/tag/v1.2.0).
 - Makam can be now obtained from the fetched audio metadata 
 - Updated the versions of [ahenkidentifier](https://github.com/sertansenturk/ahenkidentifier/releases/tag/v1.4.0) and [symbtrdataextractor](https://github.com/sertansenturk/symbtrdataextractor/releases/tag/v2.0.0-alpha.3)

#### tomato v0.5.0
 - Analysis can be run with partial success when some inputs are not available or some methods fails (Issue [#24](https://github.com/sertansenturk/tomato/issues/24))

#### tomato v0.4.0
 - Created IO, Plotter and ParamSetter classes
 - Refactored the code to use the methods from above classes for shared processes
 - All output variables are now in snake_case
 - Better saving and loading
 - Improved code quality

#### tomato v0.3.0
 - Added joint audio-score analysis
 - Minor improvement and bug fixes in SymbTrAnalyzer and AudioAnalyzer classes

#### tomato v0.2.0
 - Added SymbTr-score analysis
 - Simplified and improved the installation process

#### tomato v0.1.0
 - Added audio analysis
