#include "ExpectedMiniMax.h"
#include "SelectFirstAvailabelContainerStrategy.h"
#include <climits>
#include <vector>

ExpectedMinMax::ExpectedMinMax(double retrievalRate)
{
    this->retrievalRate = retrievalRate;
}

// Helper: select the stack with minimum height among candidates
Location shallowestStack(ContainerYard& yard, const std::vector<Location>& candidates)
{
    Location best(-1, -1);
    int minHeight = INT_MAX;

    for (auto& loc : candidates)
    {
        int h = yard.GetStackHeight(loc);
        if (h < minHeight)
        {
            minHeight = h;
            best = loc;
        }
    }
    return best;
}

void ExpectedMinMax::Solve(ContainerYard& containerYard)
{
    int bays = containerYard.GetNumberOfBays();
    int stacks = containerYard.GetNumberOfStacks();

    SelectFirstAvailabelContainerStrategy containerSelection;

    while (!containerYard.Empty())
    {
        int containerId = containerYard.GetNextContainerId();
        Location containerLocation = containerSelection.getSingleSourceLocation(containerYard, containerId);

        while (containerYard.GetTopContainerId(containerLocation) != containerId)
        {
            int topContainer = containerYard.GetTopContainerId(containerLocation);

            int lowestIndex = INT_MAX;
            std::vector<Location> rule1Candidates;

            for (int bay = 0; bay < bays; bay++)
            {
                for (int stack = 0; stack < stacks; stack++)
                {
                    Location loc(bay, stack);
                    if (loc == containerLocation || containerYard.HasMaximumHeight(loc))
                        continue;

                    int minLabel = INT_MAX;
                    int stackHeight = containerYard.GetStackHeight(loc);

                    for (int h = 0; h < stackHeight; h++)
                        minLabel = std::min(minLabel, containerYard.GetContainerId(loc, h));

                    if (minLabel > topContainer)
                    {
                        if (minLabel < lowestIndex)
                        {
                            lowestIndex = minLabel;
                            rule1Candidates = { loc };
                        }
                        else if (minLabel == lowestIndex)
                        {
                            rule1Candidates.push_back(loc);
                        }
                    }
                }
            }

            Location selectedLocation(-1, -1);

            if (!rule1Candidates.empty())
            {
                selectedLocation = shallowestStack(containerYard, rule1Candidates);
            }
            else
            {
                int M = INT_MIN;
                std::vector<Location> rule2Candidates;

                for (int bay = 0; bay < bays; bay++)
                {
                    for (int stack = 0; stack < stacks; stack++)
                    {
                        Location loc(bay, stack);
                        if (loc == containerLocation || containerYard.HasMaximumHeight(loc))
                            continue;

                        int minLabel = INT_MAX;
                        int stackHeight = containerYard.GetStackHeight(loc);

                        for (int h = 0; h < stackHeight; h++)
                            minLabel = std::min(minLabel, containerYard.GetContainerId(loc, h));

                        if (minLabel > M)
                        {
                            M = minLabel;
                            rule2Candidates = { loc };
                        }
                        else if (minLabel == M)
                        {
                            rule2Candidates.push_back(loc);
                        }
                    }
                }


                if (M == topContainer)
                {
                    int minCountM = INT_MAX;
                    std::vector<Location> best;

                    for (auto& loc : rule2Candidates)
                    {
                        int countM = 0;
                        for (int h = 0; h < containerYard.GetStackHeight(loc); h++)
                            if (containerYard.GetContainerId(loc, h) == M)
                                countM++;

                        if (countM < minCountM)
                        {
                            minCountM = countM;
                            best = { loc };
                        }
                        else if (countM == minCountM)
                        {
                            best.push_back(loc);
                        }
                    }

                    selectedLocation = shallowestStack(containerYard, best);
                }
                else
                {
                    selectedLocation = shallowestStack(containerYard, rule2Candidates);
                }
            }

            containerYard.Relocate(containerLocation, selectedLocation);
        }

        containerYard.Retrieve(containerLocation);
    }
}
