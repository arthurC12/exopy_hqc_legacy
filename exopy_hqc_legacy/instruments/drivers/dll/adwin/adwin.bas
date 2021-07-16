'Inputs:
'PAR_11 = FLAG to measure (0) of to set (1) voltage
'PAR_12 = channel
'PAR_13 = voltage - set of get
'PAR_14 = FLAG end of operation
#Include ADwinGoldII.inc
#Define channel Par_12 
#Define voltage Par_13 'set voltage
DIM measured as long
Event:
  If (Par_11 = 1) Then
    DAC(channel, voltage)
  Else
    If (Par_11 = 0) Then
      measured = ADC24(channel)
      voltage = measured
    EndIf
  EndIf
  Par_14 = 0