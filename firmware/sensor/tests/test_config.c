#include "config.h"
#include <assert.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
static struct sensor_config defaults(void) {
    return (struct sensor_config){.cycle_s=900,.low_cycle_s=3600,.window_ms=5000,
        .adv_ms=500,.session_s=300,.low_mv=2500,.calibrated=true,
        .dry={2655,2618},.wet={5658,5571},.name="Fern"};
}
int main(int argc, char **argv) {
    struct sensor_config c = defaults(), read;
    uint8_t wire[64], copy[64];
    sensor_config_encode(&c, wire);
    if (argc == 2 && !strcmp(argv[1], "--fixture")) {
        for (unsigned i=0; i<64; i++) printf("%02x",wire[i]);
        puts(""); return 0;
    }
    assert(sensor_config_validate(&c) == 0);
    assert(sensor_config_decode(&read,wire,64) == 0);
    sensor_config_encode(&read,copy); assert(!memcmp(copy,wire,64));
    assert(sensor_config_decode(&read,wire,63) == -EINVAL);
    for (unsigned i=0;i<64;i++) {
        if (i==3 || i==22 || i==23 || i>=44) {
            memcpy(copy,wire,64); copy[i]=1;
            assert(sensor_config_decode(&read,copy,64) == -EINVAL);
        }
    }
    memcpy(copy,wire,64); copy[0]=2; assert(sensor_config_decode(&read,copy,64)==-EINVAL);
    memcpy(copy,wire,64); copy[42]=0; assert(sensor_config_decode(&read,copy,64)==-EINVAL);
    c.cycle_s=59; assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    c.window_ms=500000; assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    c.cycle_s=60;c.window_ms=31000; assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    c.adv_ms=5000; assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    c.adv_ms=101; assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    c.low_cycle_s=800; assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    c.low_mv=799; assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    c.low_mv=800; assert(sensor_config_validate(&c)==0); c=defaults();
    c.low_mv=2000; assert(sensor_config_validate(&c)==0); c=defaults();
    c.window_ms=10000;c.adv_ms=1000; /* Existing persisted 0.2.9 settings remain valid. */
    assert(sensor_config_validate(&c)==0); c=defaults();
    c.session_s=901; assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    c.wet[0]=c.dry[0]; assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    c.dry[0]=INT32_MIN; assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    memset(c.name,'a',sizeof(c.name)); assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    c.name[0]='\n'; assert(sensor_config_validate(&c)==-EINVAL); c=defaults();
    assert(sensor_moisture(100,100,200)==0);
    assert(sensor_moisture(150,100,200)==5000);
    assert(sensor_moisture(300,100,200)==10000);
    assert(sensor_moisture(150,200,100)==5000);
    assert(sensor_moisture(INT32_MAX,INT32_MIN,INT32_MAX)==10000);
    assert(sensor_moisture(0,100,100)==0);
    assert(sensor_sleep_seconds(&c,false,10500)==889);
    assert(sensor_sleep_seconds(&c,true,10500)==3589);
    assert(sensor_sleep_seconds(&c,false,900000)==900);
    assert(sensor_sleep_seconds(&c,false,950000)==900);
    assert(sensor_config_crc((const uint8_t *)"123456789",9)==0xcbf43926);
    struct config_transaction t={0};
    uint8_t begin[]={1}, chunk[20]={2}, commit[5]={3};
    uint32_t crc=sensor_config_crc(wire,64);
    for(unsigned i=0;i<4;i++) commit[i+1]=crc>>(8*i);
    assert(sensor_config_command(&t,commit,5,&read)==-EINVAL);
    assert(sensor_config_command(&t,begin,1,&read)==0);
    assert(sensor_config_command(&t,commit,5,&read)==-EINVAL);
    for(unsigned i=0;i<64;i+=18) {
        unsigned n=64-i < 18 ? 64-i : 18;
        chunk[1]=i; memcpy(chunk+2,wire+i,n);
        assert(sensor_config_command(&t,chunk,n+2,&read)==0);
    }
    commit[1]^=1; assert(sensor_config_command(&t,commit,5,&read)==-EINVAL); commit[1]^=1;
    assert(sensor_config_command(&t,commit,5,&read)==1);
    sensor_config_encode(&read,copy); assert(!memcmp(copy,wire,64));
    assert(sensor_config_command(&t,commit,5,&read)==-EINVAL); /* no replay */
    assert(sensor_config_command(&t,begin,1,&read)==0);
    chunk[1]=63; assert(sensor_config_command(&t,chunk,4,&read)==-EINVAL);
    assert(sensor_config_command(&t,begin,0,&read)==-EINVAL);
    assert(sensor_config_command(&t,commit,5,&read)==-EINVAL); /* restarted transaction */
    puts("config: bounds, encoding, calibration, cadence, CRC and staged transactions passed");
    return 0;
}
