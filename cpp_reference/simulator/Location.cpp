#include "Location.h"

Location::Location(int bay, int stack)
{
	this->bay = bay;
	this->stack = stack;
}

int Location::GetBay() const
{
	return bay;
}

int Location::GetStack() const 
{
	return stack;
}

void Location::SetBay(int bay)
{
	this->bay = bay;
}

void Location::SetStack(int stack)
{
	this->stack = stack;
}

void Location::SetLocation(int bay, int stack)
{
	this->bay = bay;
	this->stack = stack;
}

bool Location::operator==(const Location& location) const
{
	return this->bay == location.bay && this->stack == location.stack;
}

bool Location::operator!=(const Location& location) const
{
	return !(*this == location);
}

bool Location::operator<(const Location& location) const
{
	return (this->bay < location.bay) || (this->bay == location.bay && this->stack < location.stack);
}


