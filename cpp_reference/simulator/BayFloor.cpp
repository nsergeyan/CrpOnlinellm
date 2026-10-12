#include "BayFloor.h"
#include "Location.h"

int BayFloor::GetStackIndex(Location &location) const
{
	return location.GetBay() * stackNumber + location.GetStack();
}

BayFloor::BayFloor(int bayNumber, int stackNumber)
{
	this->bayNumber = bayNumber;
	this->stackNumber = stackNumber;
	bayFloor.resize(bayNumber * stackNumber);
}
int BayFloor::GetTopContainerId(Location &location)
{
	const int floorIndex = GetStackIndex(location);
	return bayFloor[floorIndex].back();
}

int BayFloor::RemoveTopStack(Location &location)
{
	const int floorIndex = GetStackIndex(location);
	const int containerId = bayFloor[floorIndex].back();
	bayFloor[floorIndex].pop_back();
	return containerId;
}

void BayFloor::AddContainerToTop(Location &location, int containerId)
{
	bayFloor[GetStackIndex(location)].push_back(containerId);
}

int BayFloor::MoveContainer(Location &source, Location &destination)
{
	const int stackId = RemoveTopStack(source);
	AddContainerToTop(destination, stackId);
	return stackId;
}

int BayFloor::GetStackHeight(Location &location)
{
	return bayFloor[GetStackIndex(location)].size();
}

bool BayFloor::isStackEmpty(Location& location) {
	return bayFloor[GetStackIndex(location)].empty();
}

bool BayFloor::StackContainsContainer(Location &location, int containerID)
{
	int index = GetStackIndex(location);
	int size = bayFloor[index].size();
	for(int i = 0; i<size; i++)
	{
		if(bayFloor[index][i] == containerID)
		{
			return true;
		}
	}
	return false;
}

int BayFloor::GetContainerAtHeight(Location& location, int height)
{
	int index = GetStackIndex(location);
	return bayFloor[index][height];
}

std::string BayFloor::GetFloorString()
{
	std::stringstream bayFloorString;

	for(int bay=0; bay<bayNumber; bay++)
	{
		for(int stack=0; stack<stackNumber; stack++)
		{
			Location location = Location(bay, stack);
			int index = GetStackIndex(location);
			
			bayFloorString << bay << "\t" << stack ;
			
			for(int container=0; container<GetStackHeight(location); container++)
			{
				bayFloorString << "\t" << bayFloor[index].at(container);
			}
			bayFloorString << std::endl;
		}
	}

	return bayFloorString.str();
}

std::string BayFloor::GetFloorSingleString()
{
	std::stringstream bayFloorString;

	for (int bay = 0; bay < bayNumber; bay++)
	{
		for (int stack = 0; stack < stackNumber; stack++)
		{
			Location location = Location(bay, stack);
			int index = GetStackIndex(location);

			bayFloorString << bay << "\t" << stack;

			for (int container = 0; container < GetStackHeight(location); container++)
			{
				bayFloorString << "\t" << bayFloor[index].at(container);
			}
		}
	}

	return bayFloorString.str();
}
