#pragma once
#include "Location.h"
#include <map>
#include <string>
#include "ContainerYard.h"
#include <unordered_map>

class ProblemInstance
{
private:
	std::string instanceName;
	int bayNumber;
	int containerNumber;
	int stackNumber;
	int maximumStackHeight;

	bool multibay;
	bool duplicate;

	BayFloor bayFloor;
	std::unordered_map<int, Location> containerLocation;
	std::unordered_map<int, std::set<Location>> containerLocations;

	std::vector<int> containerCount;
	std::vector<int> containerWeights;
	std::vector<Event> eventList;
	
public:
	ProblemInstance(std::string instanceName, int bayNumber, int stackNumber, int containerNumber, int maximumStackHeight, BayFloor bayFloor, std::unordered_map<int, std::set<Location>> containerLocations, bool multibay, bool duplicate, std::vector<Event> eventList);
	ProblemInstance(std::string instanceName, int bayNumber, int stackNumber, int containerNumber, int maximumStackHeight, BayFloor bayFloor, std::unordered_map<int, Location> containerLocation, bool multibay, bool duplicate, std::vector<int> containerWeights, std::vector<Event> eventList);
	ContainerYard CreateContainerYard(double gantrySpeed, double trolleySpeed, double gantryAcceleration, double pickUpTime, int maxHeight = -1, double uncertainty = 1.0, int numberOfGroups = 0, bool useContainerGroups = false, bool knownBetweenGroup = false);
	std::string GetInstanceName();
	int GetNumberOfContainers();
	int GetNumberOfStacks();

private:
	void InitialiseContainerCount();
};

