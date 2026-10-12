#pragma once
#include <string>
#include "Location.h"
#include "ContainerMove.h"
#include <set>
#include <vector>
#include "BayFloor.h"
#include "ContainerRelocationSolution.h"
#include <unordered_map>

#include "Event.h"


class ContainerYard
{
private:
	std::string instanceName;
	
	int bayNumber;
	int containerNumber;
	int stackNumber;
	int maximumStackHeight;
	int currentContainerId;
	int numberOfRetrievedContainers;
	int numberOfGroups;

	BayFloor bayFloor;
	std::unordered_map<int, std::set<Location>> containerLocations;

	bool storeMoves{};
	std::vector<ContainerMove> containerMoves;

	int numberOfMoves;
	double totalExecutionTime;
	double totalFuelConsumed;
	
	double gantrySpeed;
	double trolleySpeed;
	double gantryAcceleration;
	double pickUpTime;

	double hoistEnergyConsumption = 0.9;
	double lowerEnergyConsumption = 0.02;
	double moveEnergyConsumption = 0.08;
	double craneWeight = 0.5;

	Location craneLocation = Location(0, 0);

	bool duplicate;
	bool multibay;
	bool containerWeightsSpecified = false;
	bool useContainerGroups = false;
	bool knownBetweenGroups = false;
	int currentCraneHeight;
	

	double dynamiclevel = 0.0;

	std::unordered_map<int, Location> containerLocation;

	std::vector<int> containerCount;
	std::vector<int> containerWeights;

	std::vector<Event> eventList;
	
public:
	ContainerYard(std::string instanceName, BayFloor bayFloor, std::unordered_map<int, std::set<Location>> containerLocations, std::vector<int> containerCount, int bayNumber, int containerNumber, int stackNumber, int maximumStackHeight, double gantrySpeed, double trolleySpeed, double gantryAcceleration, double pickUpTime, bool multibay, bool duplicate, double unceartainty, int numberOfGroups, bool useContainerGrousp, bool knownBetweenGroups, std::vector<Event> events);
	ContainerYard(std::string instanceName, BayFloor bayFloor, std::unordered_map<int, Location> containerLocation, std::vector<int> containerCount, int bayNumber, int containerNumber, int stackNumber, int maximumStackHeight, double gantrySpeed, double trolleySpeed, double gantryAcceleration, double pickUpTime, bool multibay, bool duplicate, std::vector<int> containerWeights, double unceartainty, int numberOfGroups, bool useContainerGrousp, bool knownBetweenGroups, std::vector<Event> events);

	int GetNextContainerId();
	int GetTopContainerId(Location &location);
	int GetNumberOfRemainingContainers();
	int GetNumberOfContainers();
	int GetNumberOFRetrieved();
	bool Empty();
	void Relocate(Location source, Location destination);
	void PutContainer(int containerID, Location location);
	void Retrieve(Location location);
	int GetStackHeight(Location location);
	bool isStackEmpty(Location& location);
	int GetMaxStackHeight();
	int GetNumberOfMoves();
	double GetTotalFuelConsumed();
	int GetContainerId(Location &location, int height);
	int GetMinimumStack(Location& location);
	bool isWellLocated(Location& location, int height);
	bool isNonLocated(Location& location, int height);
	int DetermineMaximumStackHeightOnPath(Location& source, Location& destination);

	double CalculateTime(const Location& source, const Location& destination);
	int CalculateDistanceToSource(Location& location);
	int CalculateDistance(Location& source, Location& destination);
	double CalculateEnergyConsumption(Location& source, Location& destination, int containerId, bool noContainer);
	const std::set<Location>& GetContainerLocations(int containerId);
	const Location& GetContainerLocation(int containerId);
	const int getCurrentCraneHeight();

	double getContainerWeight(int containerId);
	double getMaximumWeightOfContainers();
	int GetContainerWithMaxID(Location& location);
	int GetContainerWithMinID(Location& location);
	int reshuffleIndex(Location& location, int containerId);
	int calculateAverageContainerID(Location& location);
	int ContainersAbove(Location& location);
	int GetNumberOfBlocked(Location& location, int containerId);
	int GetWellLocatedCount(Location& location);
	int GetBadLocatedCount(Location& location);
	int GetHeightofLowerIndex(Location& location, int containerId);
	int GetNumberOfCurrentContainers(Location& location);
	int GetHeightOfCurrent(Location& location);
	int GetNumberOfDifferentIndices(Location& location);
	int GetChainLengthOfCurrentContainerId(Location& location);
	int GetTopMaxChainLength(Location& location);
	int NumberOfHoisted(Location& location, Location& source);
	int NumberOfLowered(Location& location, Location& source);
	int WillNeedToBeReshuffled(Location& location, int containerId);
	double CalculateTightness(Location& location, int containerId);
	int MaximumKnownContainer();
	int GetNumberOfUknown(Location& location);

	void Simulate(const std::vector<ContainerMove> &containerMoves);
	void PerformMove(ContainerMove& containerMove);

	int GetNumberOfBays();
	int GetNumberOfStacks();
	double GetTotalExecutionTime();
	
	ContainerRelocationSolution GetSolution();
	void ShouldStoreMoves(bool shouldStore);
	const Location& GetCraneLocation();

	bool HasMaximumHeight(Location& location);
	bool HasDuplicates();
	
	std::string GetCurrentYardString();
	std::string GetCurrentYardStringSingleRow();
	int GetHighestContainerPosition(Location location, int containerId);

	int GetRemainingNumberOfContainersOfId(int containerId);
	int GetNumberOfStacksWithEmptyPlaces();
	int GetContainerGroupSize();
	int GetContainerGroup(int containerId);
	int GetCurrentContainerGroup();
	int GetNumberOfContainerGroups() const;

	int RemoveTopContainer(Location location);

	void setEventList(std::vector<Event> eventList);
	std::vector<Event> getEventList();
};

