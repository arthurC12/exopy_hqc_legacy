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
'PAR_1 = output voltage
'PAR_2 = ouput_channel
'Outputs:
'PAR_5 - flag End_of_operation

#Include ADwinGoldII.inc
#Define voltage Par_1 'set voltage
#Define out_channel Par_2
Event:
  if (Par_5 > 0) Then 
    DAC(out_channel, voltage) 'Output voltage
    Par_5 = 0
  EndIf
