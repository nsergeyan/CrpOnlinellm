#include "RDH.h"

#include <iostream>

#include "ContainerSourceSelectionStrategy.h"
#include "SelectFirstAvailabelContainerStrategy.h"

RDH::RDH(double retrievalRate)
{
	this->retrievalRate = retrievalRate;
}


void RDH::Solve(ContainerYard& containerYard)
{
	int bays = containerYard.GetNumberOfBays();
	int stacks = containerYard.GetNumberOfStacks();

	ContainerSourceSelectionStrategy* containerSelection = new SelectFirstAvailabelContainerStrategy();

	int countersToRetrieved = containerYard.GetNumberOfContainers() * retrievalRate;


	while (!containerYard.Empty() && containerYard.GetNumberOFRetrieved() < countersToRetrieved)
	{
		int containerId = containerYard.GetNextContainerId();
		Location containerLocation(0, 0);
		containerLocation = containerSelection->selectLocation(containerYard, containerId);

		while (containerYard.GetTopContainerId(containerLocation) != containerId)
		{
			int X = containerYard.GetTopContainerId(containerLocation);
			int smallestY= INT_MAX;
			Location selectedLocation(-1, -1);
			for (int bay = 0; bay < bays; bay++)
			{
				for (int stack = 0; stack < stacks; stack++)
				{
					Location location = Location(bay, stack);

					if (location != containerLocation && containerYard.GetMaxStackHeight()>containerYard.GetStackHeight(location))
					{
						int Y = containerYard.GetMinimumStack(location);

						if (Y > X)
						{
							if (Y == INT_MAX || smallestY > Y)
							{
								smallestY = Y;
								selectedLocation = location;
							}
						}
					}
				}
			}
			if(selectedLocation.GetBay()==-1)
			{
				for (int bay = 0; bay < bays; bay++)
				{
					for (int stack = 0; stack < stacks; stack++)
					{
						Location location = Location(bay, stack);

						if (location != containerLocation && containerYard.GetMaxStackHeight() > containerYard.GetStackHeight(location))
						{
							int Y = containerYard.GetMinimumStack(location);

							if (Y == X)
							{
								if (smallestY > Y)
								{
									smallestY = Y;
									selectedLocation = location;
								}
							}
						}
					}
				}
			}

			int largestZ = -INT_MAX;

			if (selectedLocation.GetBay() == -1)
			{
				for (int bay = 0; bay < bays; bay++)
				{
					for (int stack = 0; stack < stacks; stack++)
					{
						Location location = Location(bay, stack);

						if (location != containerLocation && containerYard.GetMaxStackHeight() > containerYard.GetStackHeight(location))
						{

							int Z = -INT_MAX+1;
							if(!containerYard.isStackEmpty(location))
							{
								Z = containerYard.GetTopContainerId(location);
							}

							if (Z < X)
							{
								if (largestZ < Z)
								{
									largestZ = Z;
									selectedLocation = location;
								}
							}
						}
					}
				}
			}

			int largest = INT_MAX;

			if (selectedLocation.GetBay() == -1)
			{
				for (int bay = 0; bay < bays; bay++)
				{
					for (int stack = 0; stack < stacks; stack++)
					{
						Location location = Location(bay, stack);

						if (location != containerLocation && containerYard.GetMaxStackHeight() > containerYard.GetStackHeight(location))
						{
							int Z = INT_MAX-1;
							if (!containerYard.isStackEmpty(location))
							{
								Z = containerYard.GetTopContainerId(location);
							}

							if (largest > Z)
							{
									largest = Z;
									selectedLocation = location;
								
							}
						}
					}
				}
			}

			containerYard.Relocate(containerLocation, selectedLocation);
			//std::cout << containerYard.GetCurrentYardString();
		}

		containerYard.Retrieve(containerLocation);
		//std::cout << containerYard->GetCurrentYardString();

	}
}
