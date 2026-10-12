#include "ContainerYard.h"
#include <utility>
#include<algorithm>
#include <iostream>
#include <unordered_set>

ContainerYard::ContainerYard(std::string instanceName, BayFloor bayFloor,
                             std::unordered_map<int, std::set<Location>> containerLocations, std::vector<int> containerCount, int bayNumber, int containerNumber,
                             int stackNumber, int maximumStackHeight, double gantrySpeed, double trolleySpeed, double gantryAcceleration, double pickUpTime, bool multibay, bool duplicate, double unceartainty, int numberOfGroups, bool useContainerGroups, bool knownBetweenGroups, std::vector<Event> events)
:
	// We suppose that the crane is at the beginning at the position 0,0 which means that it is basically located over the truck
bayFloor(std::move(bayFloor))
{
	this->instanceName = std::move(instanceName);
	this->bayNumber = bayNumber;
	this->stackNumber = stackNumber;
	this->containerLocations = std::move(containerLocations);
	this->containerCount = std::move(containerCount);
	this->containerNumber = containerNumber;
	this->maximumStackHeight = maximumStackHeight;

	this->gantrySpeed = gantrySpeed;
	this->trolleySpeed = trolleySpeed;
	this->gantryAcceleration = gantryAcceleration;
	this->pickUpTime = pickUpTime;

	this->multibay = multibay;
	this->duplicate = duplicate;

	this->dynamiclevel = unceartainty;

	this->useContainerGroups = useContainerGroups;
	this->knownBetweenGroups = knownBetweenGroups;
	this->numberOfGroups = numberOfGroups;

	currentContainerId = 1;
	numberOfMoves = 0;
	totalExecutionTime = 0;
	numberOfRetrievedContainers = 0;
	totalFuelConsumed = 0;
	this->eventList = events;
}

ContainerYard::ContainerYard(std::string instanceName, BayFloor bayFloor,
	std::unordered_map<int, Location> containerLocation, std::vector<int> containerCount, int bayNumber, int containerNumber,
	int stackNumber, int maximumStackHeight, double gantrySpeed, double trolleySpeed, double gantryAcceleration, double pickUpTime, bool multibay, bool duplicate, std::vector<int> containerWeights, double unceartainty, int numberOfGroups, bool useContainerGroups, bool knownBetweenGroups, std::vector<Event> events)
	:
	// We suppose that the crane is at the beginning at the position 0,0 which means that it is basically located over the truck
	bayFloor(std::move(bayFloor))
{
	this->instanceName = std::move(instanceName);
	this->bayNumber = bayNumber;
	this->stackNumber = stackNumber;
	this->containerLocation = std::move(containerLocation);
	this->containerCount = std::move(containerCount);
	this->containerWeights = std::move(containerWeights);
	this->containerNumber = containerNumber;
	this->maximumStackHeight = maximumStackHeight;

	this->gantrySpeed = gantrySpeed;
	this->trolleySpeed = trolleySpeed;
	this->gantryAcceleration = gantryAcceleration;
	this->pickUpTime = pickUpTime;

	this->multibay = multibay;
	this->duplicate = duplicate;

	this->dynamiclevel = unceartainty;

	this->useContainerGroups = useContainerGroups;
	this->knownBetweenGroups = knownBetweenGroups;
	this->numberOfGroups = numberOfGroups;

	currentContainerId = 1;
	numberOfMoves = 0;
	totalExecutionTime = 0;
	totalFuelConsumed = 0;
	numberOfRetrievedContainers = 0;

	if(!this->containerWeights.empty())
	{
		containerWeightsSpecified = true;
	}

	craneLocation.SetStack(-1);
	currentCraneHeight = maximumStackHeight+1;
	this->eventList = events;
}

int ContainerYard::GetNextContainerId()
{
	return currentContainerId;
}

int ContainerYard::GetTopContainerId(Location &location)
{
	int containerId = bayFloor.GetTopContainerId(location);
	if(containerId <= MaximumKnownContainer())
	{
		return containerId;
	} else
	{
		return -1;
//		return MaximumKnownContainer()+1;
	}
}

int ContainerYard::GetNumberOfRemainingContainers()
{
	return containerNumber - numberOfRetrievedContainers;
}

bool ContainerYard::Empty()
{
	return GetNumberOfRemainingContainers() == 0;
}

void ContainerYard::Relocate(Location source, Location destination)
{
	int containerId = GetTopContainerId(source);
	totalFuelConsumed += CalculateEnergyConsumption(craneLocation, source, -1, true);
	totalFuelConsumed += CalculateEnergyConsumption(source, destination, containerId, false);

	int stackId = bayFloor.MoveContainer(source, destination);
	if(storeMoves)
	{
		containerMoves.push_back(ContainerMove(source, destination));
	}

	//Position crane to source position
	//totalExecutionTime += CalculateTime(craneLocation, source);
	


	//Move from source to destination
	numberOfMoves++;
	totalExecutionTime += CalculateTime(craneLocation, source);
	totalExecutionTime += CalculateTime(source, destination);
	
	craneLocation.SetLocation(destination.GetBay(), destination.GetStack());
	
	//TODO: support this for duplicate!
	if(duplicate)
	{
		if(!bayFloor.StackContainsContainer(source, stackId))
		{
			auto sourceIt = containerLocations.at(stackId).find(source);
			containerLocations.at(stackId).erase(sourceIt);
		}

		
		containerLocations.at(stackId).insert(destination);
	} else
	{
		containerLocation.at(stackId).SetLocation(destination.GetBay(), destination.GetStack());
	}
	
}

void ContainerYard::PutContainer(int containerID, Location location)
{
	containerLocation.insert(std::make_pair(containerID, location));
	bayFloor.AddContainerToTop(location, containerID);
}

void ContainerYard::Retrieve(Location location)
{
	int containerId = GetTopContainerId(location);
	int truckStackLocation = -1;
	Location truckLocation = Location(location.GetBay(), truckStackLocation);

	totalFuelConsumed += CalculateEnergyConsumption(craneLocation, location, -1, true);
	totalFuelConsumed += CalculateEnergyConsumption(location, truckLocation, containerId, false);


	int stackId = bayFloor.RemoveTopStack(location);
	
	if (storeMoves)
	{
		containerMoves.push_back(ContainerMove(location, craneLocation));
	}
	//let's not count this
	//numberOfMoves++;
	

	//move crane to location
	//totalExecutionTime += CalculateTime(craneLocation, location);

	// NOTE: we suppose that the truck is located on the -1 position of the bay!
	
	totalExecutionTime += CalculateTime(location, truckLocation);

	craneLocation.SetLocation(location.GetBay(), -1);
	if(duplicate)
	{
		containerCount[currentContainerId]--;
		if(!bayFloor.StackContainsContainer(location, stackId))
		{
			auto sourceIt = containerLocations.at(stackId).find(location);
			containerLocations.at(stackId).erase(sourceIt);

			if(containerLocations.at(stackId).empty())
			{
				currentContainerId++;
			}
		}
	} else
	{
		currentContainerId++;
	}
	numberOfRetrievedContainers++;
}


int ContainerYard::GetStackHeight(Location location)
{
	//truck location
	if(location.GetStack()==-1)
	{
		return 1;
	}
	return bayFloor.GetStackHeight(location);
}

bool ContainerYard::isStackEmpty(Location& location) {
	return bayFloor.isStackEmpty(location);
}

int ContainerYard::GetMaxStackHeight()
{
	return maximumStackHeight;
}

int ContainerYard::GetNumberOfMoves()
{
	return numberOfMoves;
}

double ContainerYard::GetTotalFuelConsumed()
{
	return totalFuelConsumed;
}

double ContainerYard::CalculateTime(const Location &source, const Location &destination)
{

	//MARKO: not sure if this is correct
	//MARKO: should be ok now... Needs checking
	int sourceBayChange = 1;
	if(craneLocation.GetBay() == source.GetBay())
	{
		sourceBayChange = 1;
	}
	
	double timeToGetSource = sourceBayChange*gantryAcceleration + gantrySpeed * abs(source.GetBay() - craneLocation.GetBay()) + trolleySpeed * abs(source.GetStack() - craneLocation.GetStack());

	int bayChange = 1;
	if(source.GetBay()==destination.GetBay())
	{
		bayChange = 1;
	}

	double timeToGetFromSourceToDestination = pickUpTime + bayChange* gantryAcceleration + gantrySpeed * abs(destination.GetBay() - source.GetBay()) + trolleySpeed * abs(destination.GetStack() - source.GetStack());
	//std::cout << timeToGetSource + timeToGetFromSourceToDestination << std::endl;;
	return timeToGetSource + timeToGetFromSourceToDestination;
}

int ContainerYard::CalculateDistanceToSource(Location& location)
{
	Location containerLocation = GetContainerLocation(GetNextContainerId());
	return std::abs(location.GetBay() - containerLocation.GetBay()) + std::abs(location.GetStack() - containerLocation.GetStack());
}

int ContainerYard::CalculateDistance(Location& source, Location& destination)
{
	return std::abs(source.GetBay() - destination.GetBay()) + std::abs(source.GetStack() - destination.GetStack());
}

double ContainerYard::CalculateEnergyConsumption(Location& source, Location& destination, int containerId, bool noContainer)
{
	if(!containerWeightsSpecified)
	{
		return 0;
	}
	double containerWeight = craneWeight;
	if(containerId!=-1)
	{
		containerWeight += containerWeights[containerId - 1];
	}

	const int maxHeight = DetermineMaximumStackHeightOnPath(source, destination);
	const int distance = CalculateDistance(source, destination);
	int hoisted = std::max(0, maxHeight-currentCraneHeight);
	if (!noContainer)
	{
		hoisted = std::max(0, maxHeight - currentCraneHeight + 1);
	}
	currentCraneHeight += hoisted;
	int lowered = std::max(0, currentCraneHeight - GetStackHeight(destination));
	if(!noContainer)
	{
		lowered = std::max(0, currentCraneHeight - GetStackHeight(destination)-1);
	}
	currentCraneHeight -= lowered;


	double totalEnergyConsumed = containerWeight * (moveEnergyConsumption * distance + hoistEnergyConsumption * hoisted + lowerEnergyConsumption * lowered);

	if(destination.GetStack() == -1)
	{
		currentCraneHeight = maximumStackHeight+1;
		totalEnergyConsumed += craneWeight*hoistEnergyConsumption*(currentCraneHeight - 2);
	}

	return totalEnergyConsumed;
}

const std::set<Location>& ContainerYard::GetContainerLocations(int containerId)
{
	return containerLocations.at(containerId);
}

const Location& ContainerYard::GetContainerLocation(int containerId)
{
	return containerLocation.at(containerId);
}

void ContainerYard::Simulate(const std::vector<ContainerMove>& containerMoves)
{
	for(auto containerMove : containerMoves)
	{
		PerformMove(containerMove);
	}
}

void ContainerYard::PerformMove(ContainerMove& containerMove)
{
	if(containerMove.IsRelocation())
	{
		Relocate(containerMove.GetSourceLocation(), containerMove.GetDestinationLocation());
	} else
	{
		Retrieve(containerMove.GetSourceLocation());
	}
}

int ContainerYard::GetNumberOfBays()
{
	return bayNumber;
}

int ContainerYard::GetNumberOfStacks()
{
	return stackNumber;
}

double ContainerYard::GetTotalExecutionTime()
{
	return totalExecutionTime;
}

ContainerRelocationSolution ContainerYard::GetSolution()
{
	auto solution = ContainerRelocationSolution(this->instanceName, this->numberOfMoves, this->totalExecutionTime, this->totalFuelConsumed, this->containerMoves);
	return solution;
}

void ContainerYard::ShouldStoreMoves(bool shouldStore)
{
	this->storeMoves = shouldStore;
}

const Location& ContainerYard::GetCraneLocation()
{
	return craneLocation;
}

const int ContainerYard::getCurrentCraneHeight() {
	return currentCraneHeight;
}

bool ContainerYard::HasMaximumHeight(Location& location)
{
	return maximumStackHeight == bayFloor.GetStackHeight(location);
}

bool ContainerYard::HasDuplicates()
{
	return duplicate;
}

std::string ContainerYard::GetCurrentYardString()
{
	return bayFloor.GetFloorString();
}

std::string ContainerYard::GetCurrentYardStringSingleRow()
{
	return bayFloor.GetFloorSingleString();
}

int ContainerYard::GetHighestContainerPosition(Location location, int containerId)
{
	int stackHeight = bayFloor.GetStackHeight(location);
	int position = 0;
	for(int i = 0; i<stackHeight; i++)
	{
		if(bayFloor.GetContainerAtHeight(location,i)==containerId)
		{
			position = i;
		}
	}
	return position;
}

int ContainerYard::GetRemainingNumberOfContainersOfId(int containerId)
{
	return containerCount[containerId];
}

int ContainerYard::GetNumberOfContainers()
{
	return containerNumber;
}

int ContainerYard::GetNumberOFRetrieved()
{
	return numberOfRetrievedContainers;
}

int ContainerYard::GetNumberOfStacksWithEmptyPlaces()
{
	int numberOfFreeStacks = stackNumber*bayNumber;
	for(int i =0; i< bayNumber; i++)
	{
		for(int j=0; j<stackNumber; j++)
		{
			Location l = Location(i, j);
			if(bayFloor.GetStackHeight(l) == maximumStackHeight)
			{
				numberOfFreeStacks--;
			}
		}
	}
	return numberOfFreeStacks;
}

int ContainerYard::GetContainerGroupSize()
{
	return containerNumber / numberOfGroups;
}

int ContainerYard::GetContainerGroup(int containerId)
{
	int groupId = containerId / (GetContainerGroupSize()+1) +1 ;
	return groupId * (GetContainerGroupSize()+1);
}

int ContainerYard::GetCurrentContainerGroup()
{
	int currentContainerId = GetNextContainerId();
	return GetContainerGroup(currentContainerId);
}

int ContainerYard::GetNumberOfContainerGroups() const
{
	return numberOfGroups;
}

int ContainerYard::RemoveTopContainer(Location location)
{
	return bayFloor.RemoveTopStack(location);
}

void ContainerYard::setEventList(std::vector<Event> eventList)
{
	this->eventList = std::move(eventList);
}

std::vector<Event> ContainerYard::getEventList()
{
	return eventList;
}


int ContainerYard::GetContainerId(Location &location, int height)
{
	int containerId = bayFloor.GetContainerAtHeight(location, height);
	//std::cout << containerId << " " << GetContainerGroup(containerId) << std::endl;
	
	if (containerId == GetNextContainerId())
	{
		return containerId;
	}
	if (useContainerGroups)
	{
		int containerGroup = GetContainerGroup(containerId);
		int currentContainerGroupId = GetCurrentContainerGroup();

		if (knownBetweenGroups && currentContainerGroupId == containerGroup)
		{
			return containerId;
		}
		int containerGroupId = GetContainerGroup(containerId);
		return containerGroupId;
	}

	if (containerId <= MaximumKnownContainer())
	{
		return containerId;
	}
	else
	{
		return -1;
		//return MaximumKnownContainer()+1;
	}
}


bool ContainerYard::isWellLocated(Location& location, int height){

	if (height == 0) // height 0 is the lowest one
		return true;
	
	int current = GetContainerId(location, height);

	if(current==-1)
	{
		return false;
	}

	for (int i = height - 1; i >= 0; i--) {
		int containerOnStack = GetContainerId(location, i);
		if(containerOnStack == -1)
		{
			continue;
		}
		if (current > containerOnStack) {
			return false;
		}
	}

	return true;
}

bool ContainerYard::isNonLocated(Location& location, int height) {

	return !(isWellLocated(location, height));
}

int ContainerYard::DetermineMaximumStackHeightOnPath(Location& source, Location& destination)
{
	int maximumHeight = 0;
	int initialBay = source.GetBay();
	int sourceStack = source.GetStack();
	if(sourceStack<destination.GetStack())
	{
		sourceStack += 1;
	} else
	{
		sourceStack -= 1;
	}
	int startStackIndex = std::min(sourceStack, destination.GetStack());
	int endStackIndex = std::max(sourceStack, destination.GetStack());
	
	for(int stackIndex = startStackIndex; stackIndex<=endStackIndex; stackIndex++)
	{
		int height = this->GetStackHeight(Location(initialBay, stackIndex));
		if(maximumHeight<height)
		{
			maximumHeight = height;
		}
	}

	int startBayIndex = std::min(source.GetBay(), destination.GetBay());
	int endBayIndex = std::max(source.GetBay(), destination.GetBay());

	for (int bayIndex = startBayIndex+1; bayIndex <= endBayIndex; bayIndex++)
	{
		int height = this->GetStackHeight(Location(bayIndex, destination.GetStack()));
		if (maximumHeight < height)
		{
			maximumHeight = height;
		}
	}

	return maximumHeight;
}

int ContainerYard::GetMinimumStack(Location& location) {
	int minimumValue = INT_MAX;
	for (int height = 0; height < GetStackHeight(location); height++)
	{
		int containerId = GetContainerId(location, height);
		if(containerId==-1)
		{
			continue;
		}
		if (minimumValue > containerId)
		{
			minimumValue = containerId;
		}
	}
	return minimumValue;
}

double ContainerYard::getContainerWeight(int containerId) {
	if (containerId != -1)
		return containerWeights[containerId - 1];
	else
		return craneWeight;
}

double ContainerYard::getMaximumWeightOfContainers() {
	return *max_element(containerWeights.begin(), containerWeights.end());
}

int ContainerYard::GetContainerWithMaxID(Location &location)
{
	int maximumID = -1;
	for (int height = 0; height < GetStackHeight(location); height++)
	{
		int containerOnStack = GetContainerId(location, height);
		if (containerOnStack == -1)
		{
			continue;
		}
		if (maximumID < containerOnStack)
		{
			maximumID = containerOnStack;
		}
	}
	return maximumID;
}

int ContainerYard::GetContainerWithMinID(Location& location)
{
	int maximumID = 99999;
	for (int height = 0; height < GetStackHeight(location); height++)
	{
		int containerOnStack = GetContainerId(location, height);
		if (containerOnStack == -1)
		{
			continue;
		}
		if (maximumID > containerOnStack)
		{
			maximumID = containerOnStack;
		}
	}
	return maximumID;
}


int ContainerYard::reshuffleIndex(Location& location, int containerId)
{
	int reshuffleIndex = 0;

	for (int height = 0; height < GetStackHeight(location); height++)
	{
		int containerOnStack = GetContainerId(location, height);
		if(containerOnStack == -1)
		{
			continue;
		}
		if (containerId > containerOnStack)
		{
			reshuffleIndex++;
		}
	}
	return  reshuffleIndex;
}

int ContainerYard::calculateAverageContainerID(Location& location)
{
	if (GetStackHeight(location) == 0)
	{
		return 0;
	}

	double average = 0;
	int consideredContainers = 0;
	for (int height = 0; height < GetStackHeight(location); height++)
	{
		int containerOnStack = GetContainerId(location, height);
		if(containerOnStack == -1)
		{
			continue;
		}
		consideredContainers++;
		average += containerOnStack;
	}
	
	return average / consideredContainers;
}

int ContainerYard::ContainersAbove(Location& location)
{
	int heightOfNext = 0;
	int containerToBeMoved = GetNextContainerId();
	for (int height = 0; height < GetStackHeight(location); height++)
	{
		if (GetContainerId(location, height) == containerToBeMoved)
		{
			heightOfNext = height;
			break;
		}
	}
	return GetStackHeight(location) - heightOfNext;
}

int ContainerYard::GetNumberOfBlocked(Location& location, int containerId)
{ 
	int blocked = 0;



	for (int height = 0; height < GetStackHeight(location); height++) {
		int containerOnStack = GetContainerId(location, height);
		if(containerOnStack==-1)
		{
			continue;
		}
		if ( containerOnStack< containerId) {
			blocked++;
		}
	}

	return blocked;
}

int ContainerYard::GetWellLocatedCount(Location& location)
{
	int good = 0;

	for (int height = 0; height < GetStackHeight(location); height++) {
		if (isWellLocated(location, height)) {
			good++;
		}
	}
	return good;
}

int ContainerYard::GetBadLocatedCount(Location& location)
{
	int bad = 0;

	for (int height = 0; height < GetStackHeight(location); height++) {
		if (isNonLocated(location, height)) {
			bad++;
		}
	}
	return bad;
}

int ContainerYard::GetHeightofLowerIndex(Location& location, int containerId)
{
	int h = 0;
	for (int height = 0; height < GetStackHeight(location); height++)
	{
		int containerOnStack = GetContainerId(location, height);
		if(containerOnStack==-1)
		{
			continue;
		}
		if (containerId > containerOnStack)
		{
			h = height;
			break;
		}
	}
	return h;
}

int ContainerYard::GetNumberOfCurrentContainers(Location& location)
{
	int currentContainer = GetNextContainerId();
	int currentContainerCount = 0;
	for (int i = 0; i < GetStackHeight(location); i++)
	{
		if (GetContainerId(location, i) == currentContainer) {
			currentContainerCount++;
		}
	}
	return currentContainerCount;
}

int ContainerYard::GetHeightOfCurrent(Location& location)
{
	int height = -1;
	for (int i = 0; i < GetStackHeight(location); i++)
	{
		if (GetContainerId(location, i) == GetNextContainerId())
		{
			height = i;
		}
	}
	return height;
}

int ContainerYard::GetNumberOfDifferentIndices(Location& location)
{
	std::unordered_set<int> indices;
	for (int i = 0; i < GetStackHeight(location); i++)
	{
		indices.insert(GetContainerId(location, i));
	}
	return indices.size();
}

int ContainerYard::GetChainLengthOfCurrentContainerId(Location& location)
{
	int maxChain = 0;
	int currChain = 0; 
	for (int i = 0; i < GetStackHeight(location); i++)
	{
		if (GetContainerId(location, i) == GetNextContainerId())
		{
			currChain++;
		}
		else if (currChain > maxChain)
		{
			maxChain = currChain;
			currChain = 0;
		}
		else
		{
			currChain = 0;
		}
	}
	if (currChain > maxChain)
	{
		maxChain = currChain;
	}
	return maxChain;
}

int ContainerYard::GetTopMaxChainLength(Location& location)
{
	int maxChain = 0;
	for (int i = GetStackHeight(location) - 1; i >= 0; i--)
	{
		if (GetContainerId(location, i) == GetNextContainerId())
		{
			maxChain++;
		}
		else if (maxChain > 0)
		{
			break;
		}
	}
	return maxChain;
}

int ContainerYard::NumberOfHoisted(Location& location, Location& source)
{
	// get current Crane Location and height
	Location craneLocation = GetCraneLocation();
	int craneHeight = getCurrentCraneHeight();

	// find the maxHeight on path where crane is to source
	const int maxHeight_to_source = DetermineMaximumStackHeightOnPath(craneLocation, source);
	int hoisted = std::max(0, maxHeight_to_source - craneHeight);

	//change craneHeight
	craneHeight += hoisted; 

	//move crane to source and then lowered to pick up the container
	int lowered = std::max(0, craneHeight - GetStackHeight(source));
	craneHeight -= lowered;

	//find the maxHeigth on path from source to location and add 1 because the container is moving
	const int maxHeight_from_source = DetermineMaximumStackHeightOnPath(source, location);
	hoisted += std::max(0, maxHeight_from_source - craneHeight + 1);

	return hoisted;
}

int ContainerYard::NumberOfLowered(Location& location, Location& source)
{
	// get current Crane Location and height
	Location craneLocation = GetCraneLocation();
	int craneHeight = getCurrentCraneHeight();

	// find the maxHeight on path where crane is to source
	const int maxHeight_to_source = DetermineMaximumStackHeightOnPath(craneLocation, source);
	int hoisted = std::max(0, maxHeight_to_source - craneHeight);

	//change craneHeight
	craneHeight += hoisted;

	//move crane to source and then lowered to pick up the container
	int lowered = std::max(0, craneHeight - GetStackHeight(source));
	craneHeight -= lowered;

	//find the maxHeigth on path from source to location and add 1 because the container is moving
	const int maxHeight_from_source = DetermineMaximumStackHeightOnPath(source, location);
	hoisted += std::max(0, maxHeight_from_source - craneHeight + 1);

	//add hoisted to craneHeight, and move crane to location
	craneHeight += hoisted;

	//determine lowered
	lowered += std::max(0, craneHeight - GetStackHeight(location) - 1);

	return lowered;
}


int ContainerYard::WillNeedToBeReshuffled(Location& location, int containerId)
{
	int blocked = 0;

	for (int height = 0; height < GetStackHeight(location); height++) {
		if(GetContainerId(location, height) == -1)
		{
			continue;
		}
		if (GetContainerId(location, height) < containerId) {
			blocked++;
			break;
		}
	}

	return blocked;
}

double ContainerYard::CalculateTightness(Location& location, int containerId){
	int ts = GetNumberOfContainers();
	if (!isStackEmpty(location))
		ts = GetMinimumStack(location);

	int C =GetNumberOfContainers();
	//TODO is this a bug, because this will be int and not float?
	return (ts - containerId - 1) / C;
}

int ContainerYard::MaximumKnownContainer()
{
	int containerId = GetNextContainerId() + dynamiclevel * GetNumberOfContainers();
	return containerId;
}

int ContainerYard::GetNumberOfUknown(Location& location)
{
	int unknown = 0;
	for (int height = 0; height < GetStackHeight(location); height++) {
		int containerId = bayFloor.GetContainerAtHeight(location, height);
		if (containerId > MaximumKnownContainer())
		{
			unknown++;
		}
	}

	return unknown;
}