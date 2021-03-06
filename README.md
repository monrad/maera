# Maera
Maera is a tool that is able to generate latency maps from RIPE ATLAS data

# Warning
This tool will eat up all your RIPE ATLAS credits if you are not careful.

# Install
  * Explain which modules are needed to run the programs
    * brew install homebrew/python/scipy
    * brew install matplotlib
    * brew install matplotlib-basemap
    * pip install configobj
    * pip install pyresample
    * pip install requests
    * pip install ripe.atlas.sagan[fast]
    * pip install https://github.com/RIPE-NCC/ripe-atlas-cousteau/zipball/latest

# Naming
Maera was the daugther of Atlas.

# Example of output
![EU Google Public DNS](http://monrad.github.io/maera/img/google-public-dns-a.google.com.20150310T2147ortho2_eu_map.png "EU Google Public DNS")

# Work to be done
  * Make a simple usage guide
  * Write better python code
  * Consider putting the .ast files into a db (sqlite)
  * More progress information from the generate_measurement tool
