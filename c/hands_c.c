
void overlap(int hour) {
    double temp_hour, temp_minute, temp_second;
    /* zero index hour */
    if (hour == 12) {
	hour -= 12;
    }
    temp_hour = hour;
    temp_minute = 60.0 * temp_hour / 11.0;
    temp_hour += floor(temp_minute/60);
    temp_minute -= 60.0 * floor(temp_minute/60);
    temp_second = temp_minute - floor(temp_minute);
    temp_second *= 60;
    temp_second = floor(temp_second);
    temp_minute = floor(temp_minute);
    if (temp_hour == 0) {
	temp_hour += 12;
    }
    printf("%.0f:", temp_hour);
    if (temp_minute < 10) {
	printf("0%1.0f", temp_minute);
    } else {
	printf("%2.0f", temp_minute);
    }
    if (temp_minute < 10) {
	printf(":0%1.0f\n", temp_second);
    } else {
	printf(":%2.0f\n", temp_second);
    }
}

int main (int argc, char ** argv) {
    if (argc <= 1) {
	return EXIT_SUCCESS;
    }
    while (argc > 1) {
	overlap(atoi(argv[1]));
	argv++ ; argc--;
    }
    return EXIT_SUCCESS;
}
