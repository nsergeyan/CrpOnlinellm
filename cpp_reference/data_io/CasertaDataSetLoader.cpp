#include "CasertaDataSetLoader.h"

#include "StringUtils.h"
#include <filesystem>
#include <iostream>
#include <fstream>
#include "Location.h"
#include <unordered_map>

namespace fs = std::filesystem;

DataSet CasertaDataSetLoader::Load(string path)
{
	const fs::path rootPath{ path };
	DataSet ds;
	
	for(const auto & file: fs::directory_iterator(path))
	{
		if (file.is_regular_file()) {
			ds.AddProblemInstance(LoadInstanceFromFile(file.path().string()));
		}
	}

	return ds;
}

void CasertaDataSetLoader::Load(string path, DataSet& dataSet)
{
	for (const auto& file : fs::directory_iterator(path))
	{
		if (file.is_regular_file()) {
			dataSet.AddProblemInstance(LoadInstanceFromFile(file.path().string()));
		}
	}
}

ProblemInstance CasertaDataSetLoader::LoadInstanceFromFile(string pathString)
{
	const fs::path path{ pathString };
	
	const string delimiter(" ");
	std::ifstream fstream{ path };
	string line;

	getline(fstream, line);
	auto split = StringUtils::Split(line, delimiter);
	//In these instances we only have one bay!
	int bayNumber = 1;
	int stackNumber = stoi(split[0]);
	int containerNumber = stoi(split[1]);

	BayFloor bayFloor(bayNumber, stackNumber);
	std::unordered_map<int, Location> containerLocations;
	
	int currentStack = 0;
	int currentBay = 0;

	string fileInfoPart = path.filename().string().substr(4);
	string fileDelimiter("-");
	auto fileSplit = StringUtils::Split(fileInfoPart, fileDelimiter);

	//by default the caserta dataset defines that the maximum height is stack height + 2
	int maximumStackHeight = stoi(fileSplit[0]) + 2;

	//The Caserta datasets are by default single bay and without duplicate stack IDs
	bool multibay = false;
	bool duplicate = false;
	
	while (getline(fstream, line))
	{
		split = StringUtils::Split(StringUtils::trim_copy(line), delimiter);
		auto containerLocation = Location(currentBay, currentStack);

		//We must skip the first since it denotes only the number of containers in this stack
		for (int i = 1; i < split.size(); i++)
		{
			int containerId = stoi(split[i]);
			
			bayFloor.AddContainerToTop(containerLocation, containerId);

			containerLocations.insert(make_pair(containerId, containerLocation));
		}
		currentStack++;
	}

	const fs::path weightPath { path.parent_path().generic_string() +"/" + "weights" + "/" + path.filename().generic_string()};
	vector<int> weights;
	if(fs::exists(weightPath))
	{
		ifstream weightFile{ weightPath };
		while(getline(weightFile, line))
		{
			auto split = StringUtils::Split(line, " ");
			weights.push_back(stoi(split[1]));
		}
	}


	string fileName = path.filename().string();
	std::vector<Event> eventList;

	return ProblemInstance(fileName, bayNumber, stackNumber, containerNumber, maximumStackHeight, bayFloor, containerLocations, multibay, duplicate, weights, eventList);
}
