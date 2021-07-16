'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 1
' Initial_Processdelay           = 3000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = High
' Version                        = 1
' ADbasic_Version                = 6.3.1
' Optimize                       = Yes
' Optimize_Level                 = 1
' Stacksize                      = 1000
' Info_Last_Save                 = DESKTOP-EBA7GLF  DESKTOP-EBA7GLF\sergi
'<Header End>
'Inputs:
'PAR_3 = input channel
'Outputs:
'PAR_4 = Measured value, 24 bit
'PAR_6 - flag End_of_operation

#Include ADwinGoldII.inc
#Define in_channel Par_3
DIM measured as long
INIT:
  measured = 0
EVENT:
  measured = ADC24(in_channel) 'Output voltage
  Par_4 = measured
  Par_6 = 0
