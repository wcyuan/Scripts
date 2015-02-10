#include <iostream> 
#include <sstream> 
#include <algorithm> 
   
using namespace std; 

template void std::__reverse<char*>(char*, char*, std::random_access_iterator_tag);
   
bool int_to_base36(long long n, string& buf) 
{ 
     static const char digit_chars[] = 
	 "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"; 
     static const int base = 36; 
   
     // XXX deal with negative values? 
   
     ostringstream os; 
   
     if (n == 0) { 
         os << "0"; 
     } 
     else { 
         while (n > 0) { 
             os << digit_chars[n % base]; 
             n /= base; 
         } 
     } 
   
     buf = os.str(); 
     reverse(buf.begin(), buf.end()); 
   
     return true; 
} 

int main (int argc, char ** argv) {    
    string strbuf;
    char *end;
    argc;
    long long n = strtoll(argv[1], &end , 10);
    if (*end || end == argv[1] || n <= 0) {
	std::cerr << "Can't parse argv.  "
		  << argv[1]
		  << std::endl;
	return 1;
    }
    if (!int_to_base36(n, strbuf)) {
	std::cerr << "Can't convert n into base 36.  "
		  << argv[1]
		  << " -> " << n
		  << " -> " << strbuf
		  << std::endl;
	return 1;
    }
    std::cout << strbuf << std::endl;
    return 0;
}
