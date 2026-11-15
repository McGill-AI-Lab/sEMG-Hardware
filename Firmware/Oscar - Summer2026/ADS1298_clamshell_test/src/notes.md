Reading notes from the ADS1298 for doing the following tests : 
1. simple internal register R/W operations
2. internal wg reading on channel 1
3. external wg reading on channel 1

Using the device in unipolar mode, so we have to make sure that sEMG signals do not go below "GND" level ? 

Investigate about the RLD and Wilson center terminal functionalities. 

What is lead-off detection ? 

When using the internal test signal (TEST_AMP, TEST_FREQ) the test frequency is generated as prescaled value of CLK. Does that mean we need to switch one the internal oscillator ? Maybe that's way the frequency seemed inconsistent in our very first measurements.
if not can we connect the CLK to an Arduino generated CLK signal maybe ? 

CLKSEL does what ? 
CLK is "External Master clock input or internal clock output.". Check that and get more details on that 

CLKSEL=0 means using the external clock input frequency. The datasheet specifies that this freq should be somewhere between 1.95 and 2.24 Mhz.

Gain settings : 1, 2, 3, 4, 6, 8, 12

Internal voltage reference : 

CONFIG3.VREF_4V=0 means using the internal voltage reference of 2.4V. Need to have VREFP connected to GND through two decoupling capacitors.
CONFIG3.VREF_4V=1 means using internal voltage reference of 4V

What should be the input impedance for teh channels ? Like is there any input matching we should care about

Look at how to manage the daisy chaining configuration 

The ADCs in the device offer data rates from 250 SPS to 32 kSPS

The internal oscillator generates a 2.048-MHz clock

As another test try to digitalize the internal temperature sensor (we have to use a specific mux config for that)

What does the (AVDD+AVSS)/2 entry with `CHnSET[2:0]=001` do concretely ? It biases to common mode voltage ? 
Answer : Setting `CHnSET[2:0] = 001` sets the common-mode voltage of (AVDD – AVSS) / 2 to both inputs of the channel. Use this setting to test the inherent noise of the device.
Use taht for another test !

Another test idea : generate internal waveform, but this time instead of digitalizing it, multiplex it to TESTP_PACE_OUT1 and TESTN_PACE_OUT2 so we can hook it up to the oscilloscope)

A bit register (CONFIG2.INT_TEST = 0) deactivates the internal test signals so that the test signal can be driven externally.


When hardware pace detection is not used, the TESTP_PACE_OUT1 and TESPN_PACE_OUT2 signals can be used as a multiplexed differential input channel

The differential voltage b/w TempP and TempN is proportional to temperature. The scale equation is given page 28

Assuming PGA = 1, the differential input (INP – INN) can span between –VREF to VREF. The absolute range for INP and INN must be between AVSS – 0.3 V and AVDD + 0.3 V
So does that mean that for a single power supply setup both INNx/INPx can go as low as -0.3V even if the device is powered on from gnd=0v? 

Full scale range = +/- Vref / Gain 

The CLKSEL and CLKEN are used to configure the clock.
For our purposes, we want CLKSEL=CLKEN=1 in order to connect CLK to the internally generated clock. We can also check that the internally generated clock by hooking up an oscilloscope at CLK pin. 

Rising edge of START triggers acquisition 
Falling edge of DRDY pin indicates that data can be clocked out to the ESP

Keep DIN low for the entire read operation 

There is a 24 bits status word preceeding the sample data

24 status bits + 24 bits per channel * 1 channel = 48 bits

We need to power off any unused channels so that they are not clocked out during the conversion phase (we save some useful 24 bit streams)
Positive full scale : 7FFFFFh
Negative full scale : 800000h

Make sure to be clear on how to convert 2s complement signed integers into int24. 

Continuous conversion mode

Conversions begin when the START pin is taken high for at least two tCLKs, or when the START opcode command is sent. As seen in Figure 63, the DRDY output goes high when conversions are started and goes low when data are ready. Conversions continue indefinitely until the START pin is taken low or the STOP opcode command is transmitted
o keep the converter running continuously, permanently tie the START pin high

need to wait for t_settle after issuing start opcode / pulling start high (which in any case starts acquisition)

After the serial communication is finished, always wait four or more tCLK periods before taking CS high.
"
While ADS129x is selected, the device attempts to decode and execute commands every eight serial clocks". Is it because the commands work by bytes ? (opcodes) ????

"While ADS129x is selected (CS = low), the device attempts to decode and execute commands every eight serial clocks. Therefore, present multiples of eight SCLKs every serial transfer to keep the interface in a normal operating mode. "

SCLK must be OFF whenever CS is pulled high

RDATAC = "0001 0000" => continuous data capture
RREG (read register) => "001r rrr" where rrrr is the address of the register

When in RDATAC mode, the RREG command is ignored
So need to kill RDATAC before doing any register reading (
RDATAC mode is cancelled by the stop read data continuous command (SDATAC)). Additionaly : If the device is in RDATAC mode, an SDATAC command must be issued before any other commands can be sent to the device.

IMPORTANT : The RREG opcode command reads register data. The RREG command is a two-byte opcode followed by the output of the register data. The first byte contains the command opcode and the register address. The second byte of the opcode specifies the number of registers to read – 1.

First opcode byte: 001r rrrr, where r rrrr is the starting register address.
Second opcode byte: 000n nnnn, where n nnnn is the number of registers to read – 1.

Example registers we could try reading : 

GAIN1 (05h)
CONFIG1 which contains CLK_EN, 

Read the Read-Only configuration registers to ensure the following parameters : 
* Channel ID
* Device ID

Howe do we effectively disable a channel ? Use the PowerDown bit : 
1. First set the channel to input short
2. Then Set bit 7 


05h	CH1SET	Channel 1
06h	CH2SET	Channel 2
07h	CH3SET	Channel 3
08h	CH4SET	Channel 4
09h	CH5SET	Channel 5
0Ah	CH6SET	Channel 6
0Bh	CH7SET	Channel 7
0Ch	CH8SET	Channel 8
Note : the h here just indicates the hexadecimal representation
Writing in hex : 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C

So for example to power down channel 2 write 0 on bit 7 at address 0x06

When you write to a CHnSET register, do you have to systematically write the full byte ? To avoid overwritting is it a good practice to read the initial byte then mask it with the bit of interest ? 








