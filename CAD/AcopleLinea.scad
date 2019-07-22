// Parametros del acople
diam_acople = 30;
largo_acople = 50;
eje_motor = 10;
eje_jugador = 16.5;
pris_diam = 3;
prof_motor = 25;
prof_linea = largo_acople-prof_motor;
h1 = 0.1;

module prisionero(diam, largo, altura){
    translate([0,0,altura])
        rotate([0,90,0])
            cylinder(r=diam/2, h=largo, $fn=100, center=true );
    }


difference()
{
    cylinder(r=diam_acople/2, h=largo_acople, $fn=100);
    cylinder(r=eje_motor/2, h=prof_motor+h1, $fn=100);
    translate([0,0,prof_motor])
        cylinder(r=eje_jugador/2, h=largo_acople-prof_motor+h1, $fn=100);
    
    prisionero(3, diam_acople, prof_motor/2);    
    prisionero(3, diam_acople, prof_motor + prof_linea/2);
    rotate([0,0,90])
    prisionero(3, diam_acople, prof_motor + prof_linea/2);
}

