#include <iostream.h>

class FB;

class C {
    friend class FB;
private:
    static void do_work() {
	cout << "C::do_work()" << endl;
    }
};

class FB {
public:
    virtual void do_workV() {
	cout << "FB::do_workV()" << endl;
	C::do_work();
    }
    virtual void do_workBV() {
	cout << "FB::do_workBV()" << endl;
	C::do_work();
    }
    void do_workB() {
	cout << "FB::do_workB()" << endl;
	C::do_work();
    }
};

class FD : public FB {
public:
    virtual void do_workV() {
	cout << "FD::do_workV()" << endl;
	// compilation error: inaccessible
	//C::do_work();
	cout << "can't call C::do_work()" << endl;
	FB::do_workV();
    }
    void do_workD() {
	cout << "FD::do_workD()" << endl;
	// compilation error: inaccessible
	//C::do_work();
	cout << "can't call C::do_work()" << endl;
    }
};


int main() {
    FB fb;
    fb.do_workV();
    fb.do_workBV();
    fb.do_workB();

    FD fd;
    fd.do_workV();
    fd.do_workBV();
    fd.do_workD();

    FB * fbp = &fd;
    fbp->do_workV();
    fbp->do_workBV();
    fbp->do_workB();

    return 0;
}

