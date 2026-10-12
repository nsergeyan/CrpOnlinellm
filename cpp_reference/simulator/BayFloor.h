#pragma once
#include <vector>
#include <string>
#include <sstream>

class Location;

class BayFloor
{
private:
	int bayNumber;
	int stackNumber;
	std::vector<std::vector<int>> bayFloor;
	std::vector<std::vector<int>> quality; // 
	int GetStackIndex(Location &location) const;
	
public:
	BayFloor(int bayNumber, int stackNumber);
	int GetTopContainerId(Location& location);
	int RemoveTopStack(Location& location);
	void AddContainerToTop(Location& location, int containerId);
	int MoveContainer(Location &source, Location &destination);
	int GetStackHeight(Location &location);
	bool isStackEmpty(Location &location);
	bool StackContainsContainer(Location &location, int containerID);
	int GetContainerAtHeight(Location &location, int height);
	std::string GetFloorString();
	std::string GetFloorSingleString();
};

