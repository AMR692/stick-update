#!/usr/bin/env python3

import argparse
import os
import shutil
import sys

# Parse command line arguments
parser = argparse.ArgumentParser(description='Compares manifest.txt with given directory and updates the given directory')
parser.add_argument('directory', nargs='?', help='Path to an available, working directory')

# Create mutually exclusive group for audit and dry-run flags
group = parser.add_mutually_exclusive_group()
group.add_argument('-n', '--dry-run', action='store_true', help='Print what would be done without making changes')
group.add_argument('-a', '--audit', action='store_true', help='Audit manifest.txt entries without making changes')

args = parser.parse_args()

# Validate argument combinations
if args.audit and args.directory:
	print("Error: --audit does not require a directory argument")
	sys.exit(1)

if not args.audit and not args.directory:
	print("Error: directory argument is required unless using --audit")
	sys.exit(1)

# Check for manifest.txt in current directory
manifestPath = "manifest.txt"
if not os.path.exists(manifestPath):
	print("Error: manifest.txt not found in current directory")
	sys.exit(1)

if not os.path.isfile(manifestPath):
	print("Error: manifest.txt is not a file")
	sys.exit(1)

# Read and validate each path in manifest.txt
filePaths = []
try:
	with open(manifestPath, 'r') as manifestFile:
		lineNumber = 0
		for line in manifestFile:
			lineNumber += 1
			filePath = line.strip()
			
			# Skip empty lines
			if not filePath:
				continue
			
			# Skip .DS_Store files
			if os.path.basename(filePath) == ".DS_Store":
				continue
			
			# Expand user home directory (~)
			filePath = os.path.expanduser(filePath)
			
			# Check if the file exists
			if not os.path.exists(filePath):
				print(f"Error: File '{filePath}' on line {lineNumber} does not exist")
				sys.exit(1)
			
			# Check if it's a .app (should be directory) or regular file
			if filePath.endswith('.app'):
				if not os.path.isdir(filePath):
					print(f"Error: Path '{filePath}' on line {lineNumber} is not an application")
					sys.exit(1)
			else:
				if not os.path.isfile(filePath):
					print(f"Error: Path '{filePath}' on line {lineNumber} is not a file")
					sys.exit(1)
			
			# Add to array
			filePaths.append(filePath)
			if args.audit:
				print(f"Validated: {filePath}")

except IOError as e:
	print(f"Error reading manifest.txt: {e}")
	sys.exit(1)

# If in audit mode, we're done
if args.audit:
	print(f"All {len(filePaths)} files in manifest.txt validated successfully")
	sys.exit(0)

# Continue with normal operation
workingDir = args.directory
isDryRun = args.dry_run

# Verify the directory exists and is accessible
if not os.path.exists(workingDir):
	print(f"Error: Directory '{workingDir}' does not exist")
	sys.exit(1)

if not os.path.isdir(workingDir):
	print(f"Error: '{workingDir}' is not a directory")
	sys.exit(1)

if not os.access(workingDir, os.R_OK | os.W_OK):
	print(f"Error: Directory '{workingDir}' is not accessible for read/write")
	sys.exit(1)

# Get list of all files and .app directories in working directory
workingDirFiles = []
for item in os.listdir(workingDir):
	# Skip .DS_Store files
	if item == ".DS_Store":
		continue
	itemPath = os.path.join(workingDir, item)
	if os.path.isfile(itemPath) or (item.endswith('.app') and os.path.isdir(itemPath)):
		workingDirFiles.append(item)

# Create a set of basenames from manifest for quick lookup
manifestBasenames = set()

# Check each file from manifest against working directory
for filePath in filePaths:
	basename = os.path.basename(filePath)
	manifestBasenames.add(basename)
	
	# Check if file exists in working directory
	workingFilePath = os.path.join(workingDir, basename)
	
	if not os.path.exists(workingFilePath):
		print(f"{basename}: missing")
		# Copy from manifest location to working directory
		if not isDryRun:
			if basename.endswith('.app'):
				shutil.copytree(filePath, workingFilePath)
			else:
				shutil.copy2(filePath, workingFilePath)
			print(f"Copied {basename} to working directory")
		else:
			print(f"Would copy {basename} to working directory")
		continue
	
	# Compare modification times
	manifestTime = os.path.getmtime(filePath)
	workingTime = os.path.getmtime(workingFilePath)
	
	if int(workingTime) < int(manifestTime):
		print(f"{basename}: needs update")
		# Remove old version and copy new one
		if not isDryRun:
			if basename.endswith('.app'):
				shutil.rmtree(workingFilePath)
				shutil.copytree(filePath, workingFilePath)
			else:
				shutil.copy2(filePath, workingFilePath)
			print(f"Updated {basename} in working directory")
		else:
			print(f"Would update {basename} in working directory")
	elif workingTime > manifestTime:
		print(f"{basename}: newer")
	else:
		print(f"{basename}: up-to-date")

# Check for files in working directory not in manifest
extraDir = os.path.join(workingDir, "extra")
filesToMove = []

for fileName in workingDirFiles:
	if fileName not in manifestBasenames and fileName != "extra":
		filesToMove.append(fileName)

if filesToMove:
	# Create extra directory if it doesn't exist
	if not os.path.exists(extraDir):
		if not isDryRun:
			os.makedirs(extraDir)
			print("Created 'extra' directory")
		else:
			print("Would create 'extra' directory")
	
	# Move files to extra directory
	for fileName in filesToMove:
		sourcePath = os.path.join(workingDir, fileName)
		destPath = os.path.join(extraDir, fileName)
		if not isDryRun:
			shutil.move(sourcePath, destPath)
			print(f"{fileName}: not in manifest - moved to extra/")
		else:
			print(f"{fileName}: not in manifest - would move to extra/")