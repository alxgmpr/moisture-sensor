% Compare D8 return paths in an explicitly defined common source-return fixture.
% This is not an IEC generator, device survival model, or whole-product RF model.
addpath('/usr/share/octave/packages/csxcad-0.0.35');
addpath('/usr/share/octave/packages/openems-0.0.35');
args=argv(); variant=args{1}; h=str2double(args{2}); out=args{3};
if exist(out,'dir')~=7, mkdir(out); end
FDTD=InitFDTD('NrTS',400000,'EndCriteria',1e-4);
FDTD=SetGaussExcite(FDTD,500e6,500e6);
FDTD=SetBoundaryCond(FDTD,{'PML_8','PML_8','PML_8','PML_8','PML_8','PML_8'});
CSX=InitCSX();
mesh.x=SmoothMeshLines(unique(round([-12 -6 -2:h:4 -.15 -.1 0 .1 .15 7 13]*1e6)/1e6),1.5,1.4);
mesh.y=SmoothMeshLines(unique(round([-15 -10 -6:h:1 -.25 -.1 0 .1 .25 5 11]*1e6)/1e6),1.5,1.4);
mesh.z=SmoothMeshLines(unique([-10 -5 -1.6 -.15 0 .15 .5 1 2 3 5 10]),1.5,1.4);
mesh.x=unique(round(mesh.x*1e6)/1e6); mesh.y=unique(round(mesh.y*1e6)/1e6);
assert(min(diff(mesh.x))>0.005 && min(diff(mesh.y))>0.005);
CSX=DefineRectGrid(CSX,1e-3,mesh);
CSX=AddMaterial(CSX,'FR4'); CSX=SetMaterialProperty(CSX,'FR4','Epsilon',4.2);
CSX=AddBox(CSX,'FR4',0,[-5 -9 -1.6],[7 2 0]);
CSX=AddMetal(CSX,'copper');
% Shared measurement return conductor, above PCB, tied to ground at y=-6.
CSX=AddBox(CSX,'copper',10,[-4 -8 3],[6 1 3]);
CSX=AddBox(CSX,'copper',10,[-4 -8 -.15],[6 -5.6 -.15]);
CSX=AddBox(CSX,'copper',10,[-4 -7 -.15],[6 -6 3]);
CSX=AddBox(CSX,'copper',10,[-.15 -.25 0],[.15 .25 0]);
if strcmp(variant,'baseline')
  CSX=AddBox(CSX,'copper',10,[-.2 -1.961384 0],[.2 0 0]);
  CSX=AddCylinder(CSX,'copper',10,[0 -1.961384 -1.6],[0 -1.961384 0],.25);
  p=[-.141421 .141421 2.841421 2.558579; -2.102805 -1.819963 -4.519963 -4.802805];
  CSX=AddPolygon(CSX,'copper',10,2,-1.6,p);
  CSX=AddCylinder(CSX,'copper',10,[2.7 -4.661384 -1.6],[2.7 -4.661384 0],.25);
  CSX=AddBox(CSX,'copper',10,[2.5 -6 0],[2.9 -4.661384 0]);
  CSX=AddBox(CSX,'copper',10,[2.5 -6 -.15],[2.9 -5.6 0]);
elseif strcmp(variant,'revised')
  CSX=AddBox(CSX,'copper',10,[-.5 -.15 0],[0 .15 0]);
  CSX=AddCylinder(CSX,'copper',10,[-.5 0 -.15],[-.5 0 0],.25);
  CSX=AddBox(CSX,'copper',10,[-.95 -6 -.15],[-.05 .35 -.15]);
else
  error('variant must be baseline or revised');
end
[CSX,port]=AddLumpedPort(CSX,20,1,50,[-.1 -.1 0],[.1 .1 3],[0 0 1],true);
WriteOpenEMS([out '/model.xml'],FDTD,CSX);
RunOpenEMS(out,'model.xml','--numThreads=2');
f=linspace(100e6,900e6,161); port=calcPort(port,out,f);
Z=port.uf.tot./port.if.tot;
data=[f(:),real(Z(:)),imag(Z(:)),imag(Z(:))./(2*pi*f(:))*1e9];
csvwrite([out '/impedance.csv'],data);
