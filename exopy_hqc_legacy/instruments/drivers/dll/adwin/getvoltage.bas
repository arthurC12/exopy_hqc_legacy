'Inputs:
'PAR_3 = input channel
'Outputs:
'PAR_4 = Measured value, 24 bit
'PAR_5 - flag End_of_operation

#Include ADwinGoldII.inc
#Define in_channel Par_3
DIM measured as long
INIT:
  measured = 0
EVENT:
  measured = ADC24(in_channel) 'Output voltage
  Par_4 = measured
  Par_5 = 0