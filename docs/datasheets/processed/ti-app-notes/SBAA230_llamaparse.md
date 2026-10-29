# Digital filter types in delta-sigma ADCs

<!-- Original PDF: SBAA230.pdf -->


<!-- PDF page 1 -->


*Application Note*

# **Digital Filter Types in Delta-Sigma ADCs**

![photo: Texas Instruments](page_1_image_1_v2.jpg)

*Brian Pisani*

### **ABSTRACT**

This application report discusses digital filters which are a ubiquitous feature in delta-sigma analog to digital converters (ADCs). Digital low-pass filters are essential to the functionality of a delta-sigma ADC, which relies on oversampling and noise shaping to push quantization noise out of band. There are variations between the types of digital filters used in delta-sigma ADCs that provide various benefits and drawbacks that orient them to different applications. The types of filters and the tradeoffs between them are discussed in this report.

<table>
  <caption><b>Table of Contents</b></caption>
    <tr>
      <td><b><b>1 Introduction</b></b>.............................................................................................................................................................................</td>
      <td>2</td>
    </tr>
    <tr>
      <td><b><b>2 Digital Filters in Delta-Sigma ADCs</b></b>......................................................................................................................................</td>
      <td>2</td>
    </tr>
    <tr>
      <td><b><b>3 Sinc Filter</b></b>.................................................................................................................................................................................</td>
      <td>4</td>
    </tr>
    <tr>
      <td><b><b>4 Wideband Filters</b></b>.....................................................................................................................................................................</td>
      <td>6</td>
    </tr>
    <tr>
      <td><b><b>5 References</b></b>..............................................................................................................................................................................</td>
      <td>8</td>
    </tr>
    <tr>
      <td><b><b>6 Revision History</b></b>......................................................................................................................................................................</td>
      <td>8</td>
    </tr>
</table>

<table>
  <caption><b>**List of Figures**</b></caption>
    <tr>
      <td>Figure 2-1. Spectrum of Delta-Sigma Quantization Noise and a Sinc Low-Pass Filter...............................................................</td>
      <td>2</td>
    </tr>
    <tr>
      <td>Figure 2-2. Wideband Filter Frequency Response......................................................................................................................</td>
      <td>3</td>
    </tr>
    <tr>
      <td>Figure 2-3. Sinc<sup>3</sup> Frequency Response.......................................................................................................................................</td>
      <td>3</td>
    </tr>
    <tr>
      <td>Figure 3-1. Frequency Response of Sinc<sup>1</sup>, Sinc<sup>3</sup>, and Sinc<sup>5</sup> Digital Filters.................................................................................</td>
      <td>4</td>
    </tr>
    <tr>
      <td>Figure 3-2. Step Response for Sinc<sup>1</sup>, Sinc<sup>3</sup>, and Sinc<sup>5</sup> Digital Filters.........................................................................................</td>
      <td>5</td>
    </tr>
    <tr>
      <td>Figure 3-3. Magnitude Response of the ADS124S08 Digital Filter, f<sub>DR</sub> = 20 SPS.......................................................................</td>
      <td>5</td>
    </tr>
    <tr>
      <td>Figure 4-1. Magnitude Response for the ADS127L01 Wideband Filter up to f<sub>DR</sub> .......................................................................</td>
      <td>6</td>
    </tr>
    <tr>
      <td>Figure 4-2. Response of the ADS127L01 Wideband Filter to a Unit-Step Input..........................................................................</td>
      <td>7</td>
    </tr>
</table>

### **Trademarks**

All trademarks are the property of their respective owners.


<!-- PDF page 2 -->


# **1 Introduction**

Delta-sigma analog-to-digital converters (ADCs) are different from other types of data converters in that they typically integrate digital filters. The digital filter is crucial to how delta-sigma ADCs are able to obtain fine resolution across a variety of bandwidths. This application report discusses the motivation for including a digital filter in delta-sigma ADCs, the different types of digital filters, and the tradeoffs that exist between the various types of digital filters as they relate to different applications.

# **2 Digital Filters in Delta-Sigma ADCs**

To understand why the digital filter is an important aspect in delta-sigma analog-to-digital conversion, it is critical to have a basic understanding of a delta-sigma modulator. The modulator takes its input from a sample-and-hold circuit which will sample the ADC input at a rate (f<sub>MOD</sub>) many times faster than the ADC output data rate (f<sub>DR</sub>).

The modulator consists of at least one integrator and a low-resolution ADC which quantizes the integrator output voltage into just a few bits. The modulator converts the result of the low-resolution ADC back to analog and feeds it back to the modulator input where it is subtracted from the input voltage as a means of error correction. The result is a discrete-time feedback system which allows sampled input signals to pass at unity gain, but will shape quantization noise density to be lower at low frequency and higher at high frequency.

In order to reduce higher-frequency quantization noise, the modulator output is fed to the digital low-pass filter. Subsequently, the signal of interest passes through to the output of the digital filter, while much of the higher-frequency quantization noise is filtered out.

Figure 2-1 shows quantization noise plotted with the response of a common type of low-pass digital filter found in delta-sigma ADCs called a sinc filter (its name stems from its sin(x) / x frequency response).

<table>
  <caption>**Figure 2-1. Spectrum of Delta-Sigma Quantization Noise and a Sinc Low-Pass Filter**; Magnitude (dB) vs Frequency (f<sub>MOD</sub>)</caption>
  <thead>
    <tr>
      <th>Frequency (f<sub>MOD</sub>)</th>
      <th>Digital filter response (dB)</th>
      <th>Modulator quantization noise (dB)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0</td>
      <td>-160</td>
    </tr>
    <tr>
      <th>0.025</th>
      <td>-10</td>
      <td>-110</td>
    </tr>
    <tr>
      <th>0.05</th>
      <td>-45</td>
      <td>-92</td>
    </tr>
    <tr>
      <th>0.0625</th>
      <td>-160</td>
      <td>-86</td>
    </tr>
    <tr>
      <th>0.075</th>
      <td>-85</td>
      <td>-81</td>
    </tr>
    <tr>
      <th>0.1</th>
      <td>-66</td>
      <td>-72</td>
    </tr>
    <tr>
      <th>0.125</th>
      <td>-160</td>
      <td>-66</td>
    </tr>
    <tr>
      <th>0.15</th>
      <td>-92</td>
      <td>-61</td>
    </tr>
    <tr>
      <th>0.165</th>
      <td>-87</td>
      <td>-59</td>
    </tr>
    <tr>
      <th>0.1875</th>
      <td>-160</td>
      <td>-56</td>
    </tr>
    <tr>
      <th>0.2</th>
      <td>-105</td>
      <td>-54</td>
    </tr>
    <tr>
      <th>0.22</th>
      <td>-100</td>
      <td>-52</td>
    </tr>
    <tr>
      <th>0.25</th>
      <td>-160</td>
      <td>-50</td>
    </tr>
    <tr>
      <th>0.275</th>
      <td>-109</td>
      <td>-48</td>
    </tr>
    <tr>
      <th>0.3</th>
      <td>-160</td>
      <td>-46</td>
    </tr>
    <tr>
      <th>0.325</th>
      <td>-115</td>
      <td>-45</td>
    </tr>
    <tr>
      <th>0.35</th>
      <td>-160</td>
      <td>-44</td>
    </tr>
    <tr>
      <th>0.375</th>
      <td>-119</td>
      <td>-43</td>
    </tr>
    <tr>
      <th>0.4</th>
      <td>-160</td>
      <td>-43</td>
    </tr>
    <tr>
      <th>0.425</th>
      <td>-122</td>
      <td>-42</td>
    </tr>
    <tr>
      <th>0.45</th>
      <td>-160</td>
      <td>-42</td>
    </tr>
    <tr>
      <th>0.475</th>
      <td>-124</td>
      <td>-42</td>
    </tr>
    <tr>
      <th>0.5</th>
      <td>-160</td>
      <td>-42</td>
    </tr>
  </tbody>
</table>

Sinc filters, while extremely common, are not the only types of digital low-pass filters associated with delta-sigma ~~ADCs. For example, some ADCs, like the ADS124S08, add an extra 50 Hz and 60 Hz~~ notch filter designed for applications with a lot of power-line interference. On the other hand, the ADS127L01 has a wide-bandwidth flat-passband digital filter designed for higher-frequency applications.

The digital filters in delta-sigma ADCs serve another function – decimation. These filters decimate data which is output from the modulator at f<sub>MOD</sub> by a factor known as the oversampling ratio (OSR). The relationship between f<sub>DR</sub> and f<sub>MOD</sub> is f<sub>DR</sub> = f<sub>MOD</sub> / OSR. The OSR and filter type combined determine the output bandwidth of the digital filter and overall frequency response of the ADC. Large OSRs produce small filter bandwidths, which translates to very good noise performance, simplified anti-aliasing circuitry, and reduced digital interface speeds for the host controllers.


<!-- PDF page 3 -->


![logo: Texas Instruments](page_3_image_1_v2.jpg)

[www.ti.com](http://www.ti.com)

Most digital filters in delta-sigma ADCs have a finite impulse response (FIR). These filters are inherently stable and easy to design with linear phase responses. Figure 2-2 and Figure 2-3 plot the responses of two types of FIR filters in delta-sigma ADCs side by side. Figure 2-2 shows the wideband filter in the ADS127L01. Figure 2-3 is a classic third-order sinc response filter, or sinc<sup>3</sup> like that found in the ADS124S08.

<table>
  <caption>**Figure 2-2. Wideband Filter Frequency Response**</caption>
  <thead>
    <tr>
      <th>Frequency (f<sub>DR</sub>)</th>
      <th>Magnitude (dB)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0</td>
    </tr>
    <tr>
      <th>0.1</th>
      <td>0</td>
    </tr>
    <tr>
      <th>0.2</th>
      <td>0</td>
    </tr>
    <tr>
      <th>0.3</th>
      <td>0</td>
    </tr>
    <tr>
      <th>0.4</th>
      <td>0</td>
    </tr>
    <tr>
      <th>0.45</th>
      <td>-10</td>
    </tr>
    <tr>
      <th>0.5</th>
      <td>-120</td>
    </tr>
    <tr>
      <th>0.6</th>
      <td>-120</td>
    </tr>
    <tr>
      <th>0.7</th>
      <td>-120</td>
    </tr>
    <tr>
      <th>0.8</th>
      <td>-120</td>
    </tr>
    <tr>
      <th>0.9</th>
      <td>-120</td>
    </tr>
    <tr>
      <th>1</th>
      <td>-120</td>
    </tr>
  </tbody>
</table>

<table>
  <caption>Figure 2-3. Sinc<sup>3</sup> Frequency Response</caption>
  <thead>
    <tr>
      <th>Frequency (f<sub>DR</sub>)</th>
      <th>Magnitude (dB)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0.0</th>
      <td>0</td>
    </tr>
    <tr>
      <th>0.5</th>
      <td>-10</td>
    </tr>
    <tr>
      <th>1.0</th>
      <td>-140</td>
    </tr>
    <tr>
      <th>1.5</th>
      <td>-40</td>
    </tr>
    <tr>
      <th>2.0</th>
      <td>-140</td>
    </tr>
    <tr>
      <th>2.5</th>
      <td>-53</td>
    </tr>
    <tr>
      <th>3.0</th>
      <td>-140</td>
    </tr>
    <tr>
      <th>3.5</th>
      <td>-61</td>
    </tr>
    <tr>
      <th>4.0</th>
      <td>-140</td>
    </tr>
    <tr>
      <th>4.5</th>
      <td>-66</td>
    </tr>
    <tr>
      <th>5.0</th>
      <td>-140</td>
    </tr>
    <tr>
      <th>5.5</th>
      <td>-69</td>
    </tr>
    <tr>
      <th>6.0</th>
      <td>-140</td>
    </tr>
    <tr>
      <th>6.5</th>
      <td>-71</td>
    </tr>
    <tr>
      <th>7.0</th>
      <td>-140</td>
    </tr>
    <tr>
      <th>7.5</th>
      <td>-73</td>
    </tr>
    <tr>
      <th>8.0</th>
      <td>-140</td>
    </tr>
  </tbody>
</table>

The benefit of using a wideband filter for AC measurement applications is clear from its magnitude response. Its nearly 0-dB gain until right before the Nyquist bandwidth of the data rate (f<sub>DR</sub> / 2) ensures no signal power loss for frequencies in the passband. The steep transition band limits aliasing. The sinc<sup>3</sup> filter, on the other hand, attenuates signals to –3 dB at 0.262 x f<sub>DR</sub> and transitions slowly even after f<sub>DR</sub> / 2, which would enable more out-of-band noise to fold into the bandwidth of interest. Seemingly, the wideband FIR filter would be ideal for any application; however, this excellent frequency-domain performance comes at a price.

The trade-off between the wideband filter and the sinc filter is in the time domain. The wideband filter is a very high-order filter, meaning it takes a long time to settle to a final value upon receiving a step input. In the wideband filter of the ADS127L01, it will take 84 conversions to receive a settled output. A sinc<sup>3</sup> filter settles in three conversions after a step at the input, enabling quick cycling through multiple input channels. This trade-off between frequency response and latency exists for all FIR filters.


<!-- PDF page 4 -->


![logo: Texas Instruments](page_4_image_1_v2.jpg)

# **3 Sinc Filter**

The name “sinc” comes from its frequency response, which takes the form of the sin(x) / x function. The reason the filter has this response is actually tied closely with why it is so often used in delta-sigma ADCs.

The digital filter creates a digital output code by summing the modulator output over a certain number of modulator clock periods. The ratio of the modulator rate (f<sub>MOD</sub>) of the delta-sigma ADC to its output data rate (f<sub>DR</sub>) is the OSR. This is equivalent to taking a moving average of those samples over the sampling period. Taking the moving average in the time domain translates to a first-order sinc response in the frequency domain. The sinc response is equal to zero at integer multiples of the data rate, which appear as notches in the magnitude response plot of the filter.

The amount of averaging increases when cascading multiple sinc filters in series, thus increasing the filter order. In the spectrum, this corresponds to a lower cutoff frequency and a higher stopband attenuation, which in turn reduces noise. Figure 3-1 shows the difference in the frequency responses of a first-order sinc filter (sinc<sup>1</sup>), three sinc filters in series (a third-order sinc, sinc<sup>3</sup>) and five sinc filters in series (sinc<sup>5</sup>).

<table>
  <caption>Figure 3-1. Frequency Response of Sinc¹, Sinc³, and Sinc⁵ Digital Filters — Magnitude (dB) vs Frequency (f<sub>DR</sub>)</caption>
  <thead>
    <tr>
      <th rowspan="2">Frequency (f<sub>DR</sub>)</th>
      <th colspan="3">Magnitude (dB)</th>
    </tr>
    <tr>
      <th>Sinc¹</th>
      <th>Sinc³</th>
      <th>Sinc⁵</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>0.5</th>
      <td>-4</td>
      <td>-12</td>
      <td>-20</td>
    </tr>
    <tr>
      <th>1</th>
      <td>-140</td>
      <td>-140</td>
      <td>-140</td>
    </tr>
    <tr>
      <th>1.5</th>
      <td>-13</td>
      <td>-40</td>
      <td>-66</td>
    </tr>
    <tr>
      <th>2</th>
      <td>-140</td>
      <td>-140</td>
      <td>-140</td>
    </tr>
    <tr>
      <th>2.5</th>
      <td>-18</td>
      <td>-53</td>
      <td>-88</td>
    </tr>
    <tr>
      <th>3</th>
      <td>-140</td>
      <td>-140</td>
      <td>-140</td>
    </tr>
    <tr>
      <th>3.5</th>
      <td>-21</td>
      <td>-61</td>
      <td>-101</td>
    </tr>
    <tr>
      <th>4</th>
      <td>-140</td>
      <td>-140</td>
      <td>-140</td>
    </tr>
    <tr>
      <th>4.5</th>
      <td>-23</td>
      <td>-66</td>
      <td>-110</td>
    </tr>
    <tr>
      <th>5</th>
      <td>-140</td>
      <td>-140</td>
      <td>-140</td>
    </tr>
    <tr>
      <th>5.5</th>
      <td>-25</td>
      <td>-69</td>
      <td>-115</td>
    </tr>
    <tr>
      <th>6</th>
      <td>-140</td>
      <td>-140</td>
      <td>-140</td>
    </tr>
    <tr>
      <th>6.5</th>
      <td>-26</td>
      <td>-72</td>
      <td>-119</td>
    </tr>
    <tr>
      <th>7</th>
      <td>-140</td>
      <td>-140</td>
      <td>-140</td>
    </tr>
    <tr>
      <th>7.5</th>
      <td>-27</td>
      <td>-73</td>
      <td>-121</td>
    </tr>
    <tr>
      <th>8</th>
      <td>-140</td>
      <td>-140</td>
      <td>-140</td>
    </tr>
  </tbody>
</table>

**Figure 3-1. Frequency Response of Sinc<sup>1</sup>, Sinc<sup>3</sup>, and Sinc<sup>5</sup> Digital Filters**

Looking at these responses, there does not seem to be very much bandwidth in the digital-filter output, limiting the measurable signal content. This is not a drawback in certain low-bandwidth applications. Some precision sensor applications, like temperature and pressure sensors, do not require much bandwidth for measurement, but need a good low-pass filter to reject out-of-band noise. The sinc filter fits well into these applications.

Given the application, it may be desirable to multiplex between multiple sensor inputs relatively quickly. To do this, the digital filter needs to respond to an input change and settle quickly. The sinc filter is ideal for this, too. Sinc filters offer much faster settling times relative to other digital filters with more finely tuned frequency responses. In many cases, these filters can be built to settle to a step input in a single conversion cycle.

Nevertheless, trade-offs exist even between the types of sinc filters. The higher order a sinc filter is, the longer it will take to settle – but with the bonus of better stop-band attenuation. Figure 3-2 shows how the sinc<sup>1</sup>, sinc<sup>3</sup> and sinc<sup>5</sup> filters respond to a unit step input. Note that the order of the sinc filter matches the number of samples it takes to settle to the input.


<!-- PDF page 5 -->


<table>
  <caption>Step Response of Sinc Filters — Normalized Amplitude vs. Sample</caption>
  <thead>
    <tr>
      <th>Sample</th>
      <th>Input</th>
      <th>Sinc<sup>1</sup></th>
      <th>Sinc<sup>3</sup></th>
      <th>Sinc<sup>5</sup></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>5</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>6</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>8</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>9</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>10</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>11</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>12</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>13</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>14</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>15</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>16</th>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>17</th>
      <td>1</td>
      <td>1</td>
      <td>0.20</td>
      <td>0.02</td>
    </tr>
    <tr>
      <th>18</th>
      <td>1</td>
      <td>1</td>
      <td>0.86</td>
      <td>0.28</td>
    </tr>
    <tr>
      <th>19</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>0.83</td>
    </tr>
    <tr>
      <th>20</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
    </tr>
    <tr>
      <th>21</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
    </tr>
    <tr>
      <th>22</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
    </tr>
    <tr>
      <th>23</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
    </tr>
    <tr>
      <th>24</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
    </tr>
    <tr>
      <th>25</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
    </tr>
    <tr>
      <th>26</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
    </tr>
    <tr>
      <th>27</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
    </tr>
    <tr>
      <th>28</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
    </tr>
    <tr>
      <th>29</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
    </tr>
    <tr>
      <th>30</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
    </tr>
  </tbody>
</table>

**Figure 3-2. Step Response for Sinc<sup>1</sup>, Sinc<sup>3</sup>, and Sinc<sup>5</sup> Digital Filters**

Some data converters have slightly modified sinc filters. In some industrial applications, power utility interference pollutes the environment of the equipment at 50 Hz or 60 Hz. A digital filter that has notches in its frequency response at 50 Hz or 60 Hz helps reject the utility frequency and maintain high system power-supply rejection (PSR).

In many cases, these filters can be built to settle to a step input in a single conversion cycle. However, a filter that settles within a single cycle will not have as much out-of-band rejection as an unmodified higher-order sinc filter. Figure 3-3 shows the magnitude response of the digital filter on the ADS124S08 when the data rate is set to 20 SPS using the low-latency filter. Note that this filter simultaneously rejects both 50 Hz and 60 Hz. A normal sinc filter would require a data rate at some integer divisor of 10 SPS to achieve this, since filter notches would occur at multiples of 10 Hz.

<table>
  <caption>Figure 41. Detailed View of the Magnitude Response (20 SPS) — ADS124S08 digital filter; Frequency (Hz) vs Magnitude (dB)</caption>
  <thead>
    <tr>
      <th>Frequency (Hz)</th>
      <th>Magnitude (dB)</th>
    </tr>
  </thead>
  <tbody>
    <tr><th>0</th><td>0</td></tr>
    <tr><th>10</th><td>-2</td></tr>
    <tr><th>20</th><td>-8</td></tr>
    <tr><th>30</th><td>-18</td></tr>
    <tr><th>40</th><td>-36</td></tr>
    <tr><th>50</th><td>-140</td></tr>
    <tr><th>55</th><td>-75</td></tr>
    <tr><th>60</th><td>-140</td></tr>
    <tr><th>70</th><td>-55</td></tr>
    <tr><th>80</th><td>-36</td></tr>
    <tr><th>90</th><td>-33</td></tr>
    <tr><th>100</th><td>-115</td></tr>
    <tr><th>110</th><td>-40</td></tr>
    <tr><th>120</th><td>-112</td></tr>
    <tr><th>130</th><td>-42</td></tr>
    <tr><th>140</th><td>-50</td></tr>
    <tr><th>150</th><td>-132</td></tr>
    <tr><th>155</th><td>-76</td></tr>
    <tr><th>160</th><td>-128</td></tr>
    <tr><th>170</th><td>-52</td></tr>
    <tr><th>180</th><td>-136</td></tr>
    <tr><th>185</th><td>-74</td></tr>
    <tr><th>190</th><td>-129</td></tr>
    <tr><th>200</th><td>-74</td></tr>
  </tbody>
</table>

**Figure 3-3. Magnitude Response of the ADS124S08 Digital Filter, f<sub>DR</sub> = 20 SPS**

In summary, the sinc filter is used as a basic low-pass filter in delta-sigma ADCs. Their reasonable stopband attenuation combined with their quick step response make them ideal for dc measurement applications, especially when multiplexing between several input signals.


<!-- PDF page 6 -->


# **4 Wideband Filters**

Even though delta-sigma ADCs with sinc filters are a great fit for low-bandwidth applications, the delta-sigma architecture can also be used with great success in higher bandwidth applications as well. For example, precisely measuring audio or vibration signals can be done using delta-sigma ADCs. Test and measurement equipment that requires high bandwidth is another application well-suited for delta-sigma ADCs. For these applications, a wideband filter can be used as the integrated digital filter on a delta-sigma ADC.

AC applications require a wide passband with little attenuation or ripple, but still require the precision that comes standard with the oversampling topology of a delta-sigma ADC. That is why some ADCs are designed with a wide passband filter that has a steep transition band. The ADS127L01, a 24-bit delta-sigma ADC optimized for wide-bandwidth applications, has such a filter. Figure 4-1 shows the magnitude response of the filter up to the output data rate, f<sub>DR</sub>, of the ADC, which is 512 kHz. Note how steep the transition band of the filter is around f<sub>DR</sub> / 2 – the frequency where signals begin to alias into the passband. This serves to drastically limit unwanted signals or noise from folding over. The stopband magnitude never exceeds –116 dB until the response of the filter repeats around the modulator frequency, f<sub>MOD</sub>, of the ADC.

**Figure 4-1. Magnitude Response for the ADS127L01 Wideband Filter up to f<sub>DR</sub>**

<table>
  <caption>Figure 11. Wideband Filter Response — Magnitude (dB) vs Frequency (kHz)</caption>
  <thead>
    <tr>
      <th>Frequency (kHz)</th>
      <th>Magnitude (dB)</th>
    </tr>
  </thead>
  <tbody>
    <tr><th>0</th><td>0</td></tr>
    <tr><th>32</th><td>0</td></tr>
    <tr><th>64</th><td>0</td></tr>
    <tr><th>96</th><td>0</td></tr>
    <tr><th>128</th><td>0</td></tr>
    <tr><th>160</th><td>0</td></tr>
    <tr><th>192</th><td>0</td></tr>
    <tr><th>224</th><td>-2</td></tr>
    <tr><th>240</th><td>-20</td></tr>
    <tr><th>248</th><td>-60</td></tr>
    <tr><th>256</th><td>-116</td></tr>
    <tr><th>288</th><td>-116</td></tr>
    <tr><th>320</th><td>-116</td></tr>
    <tr><th>352</th><td>-116</td></tr>
    <tr><th>384</th><td>-116</td></tr>
    <tr><th>416</th><td>-116</td></tr>
    <tr><th>448</th><td>-118</td></tr>
    <tr><th>480</th><td>-120</td></tr>
    <tr><th>512</th><td>-122</td></tr>
  </tbody>
</table>

For higher-bandwidth applications, the sinc filter is less adequate for a few reasons. First, the frequency response rolls off early and droops at relatively low frequencies. This limits the usable signal bandwidth. On the other hand, the wideband filter remains almost perfectly flat until around f<sub>DR</sub> / 2, maximizing the usable signal bandwidth for any given data rate.

Second, aliasing is more of a concern for AC applications. The sinc filter is not ideal because it does not attenuate sufficiently at half the output data rate, f<sub>DR</sub> / 2, of the ADC. Alternatively, the wideband filter features exceptional stopband attenuation, which minimizes aliasing.

For ADCs without integrated digital filters, options are limited for achieving such a steep anti-aliasing response. High-order analog anti-aliasing filters with steep roll-offs are notoriously difficult to design and are subject to component tolerances and temperature. Alternatively, it is possible to oversample the converter and digitally filter in the processor, but this comes at the cost of instruction cycles, which may be scarce in high-speed applications. A wideband filter in a delta-sigma ADC truly solves this problem with its built-in “oversample, low-pass filter, then decimate” topology.

There is a trade-off with all digital filters where superb frequency-domain performance is achieved in exchange for longer settling times. After applying a step function to the input, the digital filter of the ADS127L01 requires 84 output sample periods to settle to the final output. For this reason, wideband filters are not ideal for applications that cycle between multiple-signal source inputs.


<!-- PDF page 7 -->


Figure 4-2 shows the step response of the wideband filter of the ADS127L01.

<table>
  <caption>Figure 11. Step Response of the Wideband Filter — Normalized Amplitude vs Sample; series: Input, Output</caption>
  <thead>
    <tr>
      <th>Sample</th>
      <th>Input (Normalized Amplitude)</th>
      <th>Output (Normalized Amplitude)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0.00</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>10</th>
      <td>0.00</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>20</th>
      <td>0.00</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>30</th>
      <td>0.00</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>40</th>
      <td>0.00</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>50</th>
      <td>0.00</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>55</th>
      <td>1.00</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>60</th>
      <td>1.00</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>70</th>
      <td>1.00</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>80</th>
      <td>1.00</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>90</th>
      <td>1.00</td>
      <td>0.03</td>
    </tr>
    <tr>
      <th>92</th>
      <td>1.00</td>
      <td>1.03</td>
    </tr>
    <tr>
      <th>100</th>
      <td>1.00</td>
      <td>1.00</td>
    </tr>
    <tr>
      <th>110</th>
      <td>1.00</td>
      <td>1.00</td>
    </tr>
    <tr>
      <th>120</th>
      <td>1.00</td>
      <td>1.00</td>
    </tr>
    <tr>
      <th>130</th>
      <td>1.00</td>
      <td>1.00</td>
    </tr>
    <tr>
      <th>140</th>
      <td>1.00</td>
      <td>1.00</td>
    </tr>
    <tr>
      <th>150</th>
      <td>1.00</td>
      <td>1.00</td>
    </tr>
  </tbody>
</table>

**Figure 4-2. Response of the ADS127L01 Wideband Filter to a Unit-Step Input**

The filter has a linear phase response, which means that its group delay (the delay due to phase shifting) will be constant across frequencies. For this filter, the group delay is 42 output data samples.

The wideband digital filter in delta-sigma ADCs provides an ideal functional block for wide-bandwidth, precision-measurement signal chains where no multiplexing between different signal sources is required. The flat passband with low ripple ensures that no in-band signal content is lost, and the steep transition and excellent stopband attenuation provide flexibility in environments where anti-aliasing is critical. In addition, the precision expected from a delta-sigma ADC can still be enjoyed.


<!-- PDF page 8 -->


# **5 References**

* ADS124S08 data sheet (SBAS660)
* ADS127L01 data sheet (SBAS607)

# **6 Revision History**

NOTE: Page numbers for previous revisions may differ from page numbers in the current version.

## **Changes from Revision \* (May 2017) to Revision A (March 2023)** **Page**

* Updated the numbering format for tables, figures, and cross-references throughout the document................. 1


<!-- PDF page 9 -->


## **IMPORTANT NOTICE AND DISCLAIMER**

TI PROVIDES TECHNICAL AND RELIABILITY DATA (INCLUDING DATA SHEETS), DESIGN RESOURCES (INCLUDING REFERENCE DESIGNS), APPLICATION OR OTHER DESIGN ADVICE, WEB TOOLS, SAFETY INFORMATION, AND OTHER RESOURCES “AS IS” AND WITH ALL FAULTS, AND DISCLAIMS ALL WARRANTIES, EXPRESS AND IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE OR NON-INFRINGEMENT OF THIRD PARTY INTELLECTUAL PROPERTY RIGHTS.

These resources are intended for skilled developers designing with TI products. You are solely responsible for (1) selecting the appropriate TI products for your application, (2) designing, validating and testing your application, and (3) ensuring your application meets applicable standards, and any other safety, security, regulatory or other requirements.

These resources are subject to change without notice. TI grants you permission to use these resources only for development of an application that uses the TI products described in the resource. Other reproduction and display of these resources is prohibited. No license is granted to any other TI intellectual property right or to any third party intellectual property right. TI disclaims responsibility for, and you will fully indemnify TI and its representatives against, any claims, damages, costs, losses, and liabilities arising out of your use of these resources.

TI's products are provided subject to <mark>TI's Terms of Sale</mark> or other applicable terms available either on <mark>ti.com</mark> or provided in conjunction with such TI products. TI's provision of these resources does not expand or otherwise alter TI's applicable warranties or warranty disclaimers for TI products.

TI objects to and rejects any additional or different terms you may have proposed.

Mailing Address: Texas Instruments, Post Office Box 655303, Dallas, Texas 75265
Copyright © 2023, Texas Instruments Incorporated
