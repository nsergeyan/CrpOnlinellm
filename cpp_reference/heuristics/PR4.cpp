#include "PR4.h"
#include "SelectHighestContainerStrategy.h"
#include "SelectHighestContainerAlwaysStrategy.h"
#include "SelectMostContainersStrategy.h"
#include "SelectFirstAvailabelContainerStrategy.h"

PR4::PR4(double retrievalRate)
{
	this->retrievalRate = retrievalRate;
}

void PR4::Solve(ContainerYard& containerYard)
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
			int topContainerId = containerYard.GetTopContainerId(containerLocation);
			int lowestIndex = INT_MAX;
			Location selectedLocation(-1, -1);

			int highestIndex = INT_MIN;
			Location selectedLocationHighest(-1, -1);
			for (int bay = 0; bay < bays; bay++)
			{
				for (int stack = 0; stack < stacks; stack++)
				{
					Location location = Location(bay, stack);

					if (location != containerLocation && !containerYard.HasMaximumHeight(location))
					{
						int selectedStackLowestIndex = INT_MAX;

						//Here we find the smallest container ID value for the stack
						for (int height = 0; height < containerYard.GetStackHeight(location); height++)
						{
							int currentContainerId = containerYard.GetContainerId(location, height);
							if (selectedStackLowestIndex > currentContainerId)
							{
								selectedStackLowestIndex = currentContainerId;
							}
						}

						if (selectedStackLowestIndex > topContainerId)
						{
							if (lowestIndex > selectedStackLowestIndex)
							{
								lowestIndex = selectedStackLowestIndex;
								selectedLocation = location;
							}
							else if (selectedStackLowestIndex == INT_MAX)
							{
								lowestIndex = 0;
								selectedLocation = location;
							}
						}
						else
						{

							int numberOfSmaller = 0;
							for (int height = 0; height < containerYard.GetStackHeight(containerLocation); height++)
							{
								if (highestIndex > containerYard.GetContainerId(containerLocation, height))
								{
									numberOfSmaller++;
								}
							}

							if(numberOfSmaller>1 && ((containerYard.GetMaxStackHeight()-containerYard.GetStackHeight(location)==1))){
								highestIndex = highestIndex;
							}
							else if (highestIndex < selectedStackLowestIndex)
							{
								highestIndex = selectedStackLowestIndex;
								selectedLocationHighest = location;
							}
						}
					}
				}
			}
			if (lowestIndex < INT_MAX)
			{
				containerYard.Relocate(containerLocation, selectedLocation);
			}
			else
			{
				containerYard.Relocate(containerLocation, selectedLocationHighest);
			}
		}
		containerYard.Retrieve(containerLocation);
	}
}


Location PR4::GetMove(ContainerYard& containerYard)
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
			int topContainerId = containerYard.GetTopContainerId(containerLocation);
			int lowestIndex = INT_MAX;
			Location selectedLocation(-1, -1);

			int highestIndex = INT_MIN;
			Location selectedLocationHighest(-1, -1);
			for (int bay = 0; bay < bays; bay++)
			{
				for (int stack = 0; stack < stacks; stack++)
				{
					Location location = Location(bay, stack);

					if (location != containerLocation && !containerYard.HasMaximumHeight(location))
					{
						int selectedStackLowestIndex = INT_MAX;

						//Here we find the smallest container ID value for the stack
						for (int height = 0; height < containerYard.GetStackHeight(location); height++)
						{
							int currentContainerId = containerYard.GetContainerId(location, height);
							if (selectedStackLowestIndex > currentContainerId)
							{
								selectedStackLowestIndex = currentContainerId;
							}
						}

						if (selectedStackLowestIndex > topContainerId)
						{
							if (lowestIndex > selectedStackLowestIndex)
							{
								lowestIndex = selectedStackLowestIndex;
								selectedLocation = location;
							}
							else if (selectedStackLowestIndex == INT_MAX)
							{
								lowestIndex = 0;
								selectedLocation = location;
							}
						}
						else
						{

							int numberOfSmaller = 0;
							for (int height = 0; height < containerYard.GetStackHeight(containerLocation); height++)
							{
								if (highestIndex > containerYard.GetContainerId(containerLocation, height))
								{
									numberOfSmaller++;
								}
							}

							if (numberOfSmaller > 1 && ((containerYard.GetMaxStackHeight() - containerYard.GetStackHeight(location) == 1))) {
								highestIndex = highestIndex;
							}
							else if (highestIndex < selectedStackLowestIndex)
							{
								highestIndex = selectedStackLowestIndex;
								selectedLocationHighest = location;
							}
						}
					}
				}
			}
			if (lowestIndex < INT_MAX)
			{
				containerYard.Relocate(containerLocation, selectedLocation);
				return selectedLocation;
			}
			else
			{
				containerYard.Relocate(containerLocation, selectedLocationHighest);
				return selectedLocationHighest;

			}
		}
		containerYard.Retrieve(containerLocation);
		return Location(-1, -1);
	}
}
