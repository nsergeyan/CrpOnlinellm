#include "SelectFirstAvailabelContainerStrategy.h"

Location SelectFirstAvailabelContainerStrategy::selectLocation(ContainerYard& yard, int containerId)
{
	Location containerLocation(-1, -1);

	int bays = yard.GetNumberOfBays();
	int stacks = yard.GetNumberOfStacks();
	const int maxHeight = yard.GetMaxStackHeight();
	const int filled = bays * stacks * maxHeight;
	const int containerCount = yard.GetNumberOfRemainingContainers();


	if (yard.HasDuplicates())
	{
		auto locations = yard.GetContainerLocations(containerId);
		for (auto location : locations)
		{
			if ((filled - containerCount) >= (yard.GetStackHeight(location) - (yard.GetHighestContainerPosition(location, containerId) + 1) + yard.GetMaxStackHeight() - yard.GetStackHeight(location))) {
				if ((yard.GetNumberOfStacksWithEmptyPlaces() == 1) && (yard.GetStackHeight(location) < yard.GetMaxStackHeight()) && (yard.GetTopContainerId(location) != containerId)) {
					continue;
				}
				containerLocation = location;
				break;
			}
		}
	}
	else
	{
		return this->getSingleSourceLocation(yard, containerId);
	}
	return containerLocation;
}
