#include "PU2.h"
#include "ContainerSourceSelectionStrategy.h"
#include "SelectHighestContainerStrategy.h"
#include "SelectHighestContainerAlwaysStrategy.h"
#include "SelectMostContainersStrategy.h"
#include "SelectFirstAvailabelContainerStrategy.h"

PU2::PU2(double retrievalRate)
{
	this->retrievalRate = retrievalRate;
}

void PU2::Solve(ContainerYard& containerYard)
{
	int bays = containerYard.GetNumberOfBays();
	int stacks = containerYard.GetNumberOfStacks();

	//ContainerSourceSelectionStrategy* containerSelection = new SelectHighestContainerStrategy();
	ContainerSourceSelectionStrategy* containerSelection = new SelectFirstAvailabelContainerStrategy();

	int countersToRetrieved = containerYard.GetNumberOfContainers() * retrievalRate;

	while (!containerYard.Empty() && containerYard.GetNumberOFRetrieved() < countersToRetrieved)
	{
		int containerId = containerYard.GetNextContainerId();
		Location containerLocation = containerSelection->selectLocation(containerYard, containerId);
		
		while (containerYard.GetTopContainerId(containerLocation) != containerId)
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
			}
			else
			{
				Location selectedLocation(-1, -1);
				int containerId = -1;
				for (int bay = 0; bay < bays; bay++)
				{
					for (int stack = 0; stack < stacks; stack++)
					{
						Location location = Location(bay, stack);
						if (containerLocation == location)
						{
							continue;
						}
						//Here we find the smallest container ID value for the stack
						int selectedStackLowestIndex = INT_MAX;
						int secondSmallest = INT_MAX;

						for (int height = 0; height < containerYard.GetStackHeight(location); height++)
						{
							int currentContainerId = containerYard.GetContainerId(location, height);
							if (selectedStackLowestIndex > currentContainerId)
							{
								secondSmallest = selectedStackLowestIndex;
								selectedStackLowestIndex = currentContainerId;
							}
						}

						if (selectedStackLowestIndex == containerYard.GetTopContainerId(location) && (secondSmallest = !INT_MAX || containerYard.GetStackHeight(location) == 1))
						{
							if (selectedStackLowestIndex > containerId)
							{
								containerId = selectedStackLowestIndex;
								selectedLocation = location;
							}
						}

					}
				}

				Location selectedLocation1(-1, -1);

				//if(containerId!=-1)
				{
					int lowestIndex = INT_MAX;
					int secondSmallest = INT_MAX;

					for (int bay = 0; bay < bays; bay++)
					{
						for (int stack = 0; stack < stacks; stack++)
						{
							Location location = Location(bay, stack);

							if (location != containerLocation && selectedLocation != location && !containerYard.HasMaximumHeight(location))
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

								if (selectedStackLowestIndex > containerId)
								{
									if (lowestIndex > selectedStackLowestIndex)
									{
										lowestIndex = selectedStackLowestIndex;
										selectedLocation1 = location;
									}
									else if (selectedStackLowestIndex == INT_MAX)
									{
										lowestIndex = 0;
										selectedLocation1 = location;
									}
								}
							}
						}
					}



					if (lowestIndex < INT_MAX && selectedLocation1 != Location(-1, -1) && selectedLocation != Location(-1, -1))
					{
						//std::cout << containerYard.GetCurrentYardString();
						containerYard.Relocate(selectedLocation, selectedLocation1);
						//std::cout << containerYard.GetCurrentYardString();
						containerYard.Relocate(containerLocation, selectedLocation);
						//std::cout << containerYard.GetCurrentYardString();
					//	std::cout << std::endl;
					}
					else
					{
						containerYard.Relocate(containerLocation, selectedLocationHighest);
					}
				}

			}
		}
		containerYard.Retrieve(containerLocation);
	}
}
