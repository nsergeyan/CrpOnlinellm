#include "ReshuffleIndex.h"
#include "SelectHighestContainerStrategy.h"
#include "SelectHighestContainerAlwaysStrategy.h"
#include "SelectMostContainersStrategy.h"
#include "SelectFirstAvailabelContainerStrategy.h"

ReshuffleIndex::ReshuffleIndex(double retrievalRate)
{
	this->retrievalRate = retrievalRate;
}

void ReshuffleIndex::Solve(ContainerYard& containerYard)
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
			int reshuffleIndex = INT_MAX;
			double executionTime = DBL_MAX;
			Location selectedLocation(-1, -1);
			for (int bay = 0; bay < bays; bay++)
			{
				for (int stack = 0; stack < stacks; stack++)
				{
					Location location = Location(bay, stack);

					if (location != containerLocation && !containerYard.HasMaximumHeight(location))
					{
						int selectedStackReshuffleIndex = 0;

						for(int height = 0; height<containerYard.GetStackHeight(location); height++)
						{

							if(containerYard.GetContainerId(location, height) == -1)
							{
								continue;
							}
							if(topContainerId> containerYard.GetContainerId(location, height))
							{
								selectedStackReshuffleIndex++;
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
			//	std::cout << containerYard->GetCurrentYardString();
		}

		containerYard.Retrieve(containerLocation);
		//std::cout << containerYard->GetCurrentYardString();
	}
}
