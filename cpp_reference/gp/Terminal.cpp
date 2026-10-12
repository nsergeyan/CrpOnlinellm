#include "Terminal.h"

Terminal::Terminal(int id, std::string name, bool active)
{
	this->id = id;
	this->name = name;
	this->active = active;
}

int Terminal::GetId()
{
	return id;
}

std::string Terminal::GetName()
{
	return name;
}

bool Terminal::IsActive()
{
	return active;
}

void Terminal::SetActive(bool active)
{
	this->active = active;
}
