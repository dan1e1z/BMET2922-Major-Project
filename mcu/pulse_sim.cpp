#include "pulse_sim.h"
#include "Arduino.h"

static unsigned long pulse_sim_curr_time = 0;
static unsigned long pulse_sim_prev_time = 0;
static unsigned long pulse_sim_elapsed_periods = 0;
static uint16_t pulse_sim_data_index = 0;

int pulse_sim_data[] = {
                                  2036,1999,1973,1951,1935,1933,1931,1915,1911,1885,
                                  1885,1872,1873,1856,1861,1851,1861,1853,1840,1815,
                                  1832,1857,1871,1859,1837,1829,1824,1821,1815,1841,
                                  1904,2005,2101,2175,2217,2262,2262,2251,2242,2224,
                                  2200,2163,2114,2067,2018,1990,1970,1953,1947,1936,
                                  1927,1883,1904,1905,1904,1901,1882,1865,1869,1866,
                                  1862,1870,1872,1872,1867,1858,1861,1849,1831,1827,
                                  1823,1830,1860,1950,2043,2150,2217,2269,2285,2273,
                                  2266,2243,2227,2190,2128,
                                }; 

int pulse_sim(void) {
  /*
   * Returns a integer sample of simulated pulse sensor waveform.
   * It is best to call this function at intervals of ~20ms: this
   * was the original sample rate of the data. It may behave
   * strangely if some faster intervals are used.
   */
  pulse_sim_curr_time = micros();
  pulse_sim_elapsed_periods = (pulse_sim_curr_time - pulse_sim_prev_time)/(1000*PULSE_SIM_SAMPLE_PERIOD_MS);
  pulse_sim_data_index = (pulse_sim_data_index + pulse_sim_elapsed_periods) % 85;
  pulse_sim_prev_time = pulse_sim_curr_time;
  return pulse_sim_data[pulse_sim_data_index];
}
