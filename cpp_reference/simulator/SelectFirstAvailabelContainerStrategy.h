#pragma once
#include "ContainerSourceSelectionStrategy.h"

class SelectFirstAvailabelContainerStrategy : public ContainerSourceSelectionStrategy
{
public:
	Location selectLocation(ContainerYard& yard, int containerId) override;
};

