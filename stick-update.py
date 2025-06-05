#!/usr/bin/env python3

import argparse
import os
import shutil

# Parse command line arguments
parser = argparse.ArgumentParser(description='Update stick with specified working directory')
parser.add_argument('directory', help='Path to an available, working directory')
parser.add_argument('-n', '--dry-run', action='store_true', help='Print what would be done without making changes')
args = parser.parse_args()

workingDir = args.directory
isDryRun = args.dry_run

# Verify the directory exists and is accessible
if not os.path.exists(workingDir):
	print(f"Error: Directory '{workingDir}' does not exist")
	exit(1)

if not os.path.isdir(workingDir):
	print(f"Error: '{workingDir}' is not a directory")
	exit(1)

if not os.access(workingDir, os.R_OK | os.W_OK):
	print(f"Error: Directory '{workingDir}' is not accessible for read/write")
	exit(1)

print(f"Using working directory: {workingDir}")

# Check for manifest.txt in current directory
manifestPath = "manifest.txt"
if not os.path.exists(manifestPath):
	print("Error: manifest.txt not found in current directory")
	exit(1)

if not os.path.isfile(manifestPath):
	print("Error: manifest.txt is not a file")
	exit(1)

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
			
			# Expand user home directory (~)
			filePath = os.path.expanduser(filePath)
			
			# Check if the file exists
			if not os.path.exists(filePath):
				print(f"Error: File '{filePath}' on line {lineNumber} does not exist")
				exit(1)
			
			# Check if it's a .app (should be directory) or regular file
			if filePath.endswith('.app'):
				if not os.path.isdir(filePath):
					print(f"Error: Path '{filePath}' on line {lineNumber} should be a directory (.app)")
					exit(1)
			else:
				if not os.path.isfile(filePath):
					print(f"Error: Path '{filePath}' on line {lineNumber} is not a file")
					exit(1)
			
			# Add to array
			filePaths.append(filePath)
			print(f"Validated: {filePath}")

except IOError as e:
	print(f"Error reading manifest.txt: {e}")
	exit(1)

print(f"All {len(filePaths)} files in manifest.txt validated successfully")

# Get list of all files and .app directories in working directory
workingDirFiles = []
for item in os.listdir(workingDir):
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
	
	if workingTime < manifestTime:
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