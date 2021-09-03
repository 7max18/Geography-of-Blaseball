# Topography-of-Blaseball
The Topography of Blaseball visualizes each entry in a game's play feed as a set of points by converting each character's ASCII value to a z-value in a 3d surface, interpolating, and smoothing the result with a Gaussian filter. 
The x- and y- values are determined by order in the feed string and the play's number. 

## Requirements
This program requires numpy, plotly, scipy, and blaseball-mike.
