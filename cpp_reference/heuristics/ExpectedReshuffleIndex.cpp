#include "ExpectedReshuffleIndex.h"
#include "SelectFirstAvailabelContainerStrategy.h"
#include <climits>
#include <cfloat>

ExpectedReshuffleIndex::ExpectedReshuffleIndex(double retrievalRate)
{
    this->retrievalRate = retrievalRate; // NOT used inside ERI
}

void ExpectedReshuffleIndex::Solve(ContainerYard& containerYard)
{
	int bays = containerYard.GetNumberOfBays();
	int stacks = containerYard.GetNumberOfStacks();
	ContainerSourceSelectionStrategy* containerSelection = new SelectFirstAvailabelContainerStrategy();

	int countersToRetrieved = containerYard.GetNumberOfContainers() * retrievalRate;

	while (!containerYard.Empty() && containerYard.GetNumberOFRetrieved() < countersToRetrieved)
	{
		int containerId = containerYard.GetNextContainerId();
		Location containerLocation = containerSelection->selectLocation(containerYard, containerId);

		auto topContainerId = containerYard.GetTopContainerId(containerLocation);

		while (topContainerId != containerId)
		{
			double reshuffleIndex = INT_MAX;
			double executionTime = DBL_MAX;
			Location selectedLocation(-1, -1);
			for (int bay = 0; bay < bays; bay++)
			{
				for (int stack = 0; stack < stacks; stack++)
				{
					Location location = Location(bay, stack);

					if (location != containerLocation && !containerYard.HasMaximumHeight(location))
					{
						double selectedStackReshuffleIndex = 0;

						for (int height = 0; height < containerYard.GetStackHeight(location); height++)
						{

							if (containerYard.GetContainerId(location, height) == -1)
							{
								continue;
							}
							if (topContainerId > containerYard.GetContainerId(location, height))
							{
								selectedStackReshuffleIndex++;
							}
							else if (topContainerId == containerYard.GetContainerId(location, height))
							{
								selectedStackReshuffleIndex+=0.5;
							}
						}

						Location craneLocation = containerYard.GetCraneLocation();
						if (reshuffleIndex > selectedStackReshuffleIndex)
						{
							reshuffleIndex = selectedStackReshuffleIndex;
							selectedLocation = location;
							executionTime = containerYard.CalculateTime(craneLocation, selectedLocation);
						}
						else if (reshuffleIndex == selectedStackReshuffleIndex)
						{
							const double selectedContainerExecutionTime = containerYard.CalculateTime(craneLocation, selectedLocation);
							if (executionTime > selectedContainerExecutionTime)
							{
								reshuffleIndex = selectedStackReshuffleIndex;
								selectedLocation = location;
								executionTime = selectedContainerExecutionTime;
							}
						}
					}
				}
			}


			containerYard.Relocate(containerLocation, selectedLocation);
			topContainerId = containerYard.GetTopContainerId(containerLocation);
		}

		containerYard.Retrieve(containerLocation);
	}
}
