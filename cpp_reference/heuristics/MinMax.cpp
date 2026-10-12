#include "MinMax.h"
#include "SelectHighestContainerStrategy.h"
#include "SelectHighestContainerAlwaysStrategy.h"
#include "SelectMostContainersStrategy.h"
#include "SelectFirstAvailabelContainerStrategy.h"

MinMax::MinMax(double retrievalRate)
{
	this->retrievalRate = retrievalRate;
}

void MinMax::Solve(ContainerYard& containerYard)
{
	int bays = containerYard.GetNumberOfBays();
	int stacks = containerYard.GetNumberOfStacks();
	ContainerSourceSelectionStrategy* containerSelection = new SelectFirstAvailabelContainerStrategy();

	while (!containerYard.Empty())
	{
		int containerId = containerYard.GetNextContainerId();
		Location containerLocation = containerSelection->selectLocation(containerYard, containerId);

		int countersToRetrieved = containerYard.GetNumberOfContainers() * retrievalRate;


		while (containerYard.GetTopContainerId(containerLocation) != containerId && containerYard.GetNumberOFRetrieved() < countersToRetrieved)
		{
			int topContainer = containerYard.GetTopContainerId(containerLocation);

			int lowestIndex = INT_MAX;
			Location lowestLocation(-1, -1);

			int largestIndex = INT_MIN;
			Location largestLocation(-1, -1);

			Location selectedLocation(-1, -1);


			for (int bay = 0; bay < bays; bay++)
			{
				for (int stack = 0; stack < stacks; stack++)
				{
					Location location = Location(bay, stack);

					if (location != containerLocation && !containerYard.HasMaximumHeight(location))
					{
						int selectedStackLowestIndex = INT_MAX;

						for (int height = 0; height < containerYard.GetStackHeight(location); height++)
						{
							int currentContainerId = containerYard.GetContainerId(location, height);
							if (selectedStackLowestIndex > currentContainerId)
								selectedStackLowestIndex = currentContainerId;
							
						}

						if(selectedStackLowestIndex>topContainer)
						{
							if (lowestIndex>selectedStackLowestIndex )
							{
								lowestIndex = selectedStackLowestIndex;
								lowestLocation = location;
							}
							else if (selectedStackLowestIndex == INT_MAX)
							{
								lowestIndex = 0;
								lowestLocation = location;
							}
						} else 
						{
							if (largestIndex < selectedStackLowestIndex)
							{
								largestIndex = selectedStackLowestIndex;
								largestLocation= location;
							}
						}
					}
				}
			}
			if(lowestLocation.GetBay()!=-1)
			{
				selectedLocation = lowestLocation;
			} else
			{
				selectedLocation = largestLocation;
			}

			containerYard.Relocate(containerLocation, selectedLocation);
		}
		containerYard.Retrieve(containerLocation);
	}
}
