#pragma once
#include "Location.h"
#include "ContainerYard.h"

class ContainerSourceSelectionStrategy
{
public:
	virtual Location selectLocation(ContainerYard& yard, int containerId) = 0;
	Location getSingleSourceLocation(ContainerYard& yard, int containerId);
};

