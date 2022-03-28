#!/bin/bash

for name in $(ls -1 generated/*.blend)
do
	blender -b "${name}" -a
done