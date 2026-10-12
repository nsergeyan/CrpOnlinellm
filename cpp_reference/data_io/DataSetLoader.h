#pragma once
#include "DataSet.h"
#include <string>

using namespace std;

class DataSetLoader
{
public:
	virtual DataSet Load(string path) = 0;
	virtual void Load(string path, DataSet &dataSet) = 0;
};