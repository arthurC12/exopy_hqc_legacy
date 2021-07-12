'Inputs:
'PAR_1 = output voltage
'PAR_2 = ouput_channel
'Outputs:
'PAR_5 - flag End_of_operation

#Include ADwinGoldII.inc
#Define voltage Par_1 'set voltage
#Define out_channel Par_2
Event:
  DAC(out_channel, voltage) 'Output voltage
  Par_5 = 0