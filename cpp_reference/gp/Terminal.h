#pragma once
#include <string>

class Terminal
{
private:
	int id;
	std::string name;
	bool active;

public:
	Terminal(int id, std::string name, bool active);
	int GetId();
	std::string GetName();
	bool IsActive();
	void SetActive(bool active);
};

