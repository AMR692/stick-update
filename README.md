# stick-update

When given a directory path, makes sure the contents of the given directory match the latest versions of all files mentioned in manifest.txt.

Good for semi-automatically updating a USB stick.

	usage: stick-update.py [-h] [-n | -a] [directory]
	
	Compares manifest.txt with given directory and updates the given directory
	
	positional arguments:
	  directory      Path to an available, working directory
	
	optional arguments:
	  -h, --help     show this help message and exit
	  -n, --dry-run  Print what would be done without making changes
	  -a, --audit    Audit manifest.txt entries without making changes