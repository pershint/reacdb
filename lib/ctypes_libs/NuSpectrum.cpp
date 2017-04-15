#include "math.h"
#include "stdlib.h"
#include "stdio.h"
extern "C"
{
  double normalDist(double mu, double sigma, double x)
  {
    //This Function returns P(x) at x for a normal distribution of
    //average mu and standard deviation sigma
    double result = (1.0 / (sqrt(2.0*M_PI) * sigma)) * 
                    exp(-(pow((x - mu),2)/(2.0 * pow(sigma,2))));
    return result;
  }

  double* buildConvolvedGauss(double e, double res, double specval,
          double* e_arr, int len_earr)
  {
      double* convolvedgauss = (double*)malloc(len_earr*sizeof(double));
      for(int i=0; i<len_earr;i++)
      {
          convolvedgauss[i] = specval * normalDist(e, (res * sqrt(e)), e_arr[i]);
      }
      return convolvedgauss;
  }
  
  double* convolveWER(double* spec, double* e_arr, int nentries,double resolution)
  {
    //This Function takes each bin in the spectrum, builds a gaussian centered
    //on the value and with an integral that equals the value, and sums all of
    //The gaussians resulting from this operation on each spec bin.
    printf("Spectrum fed in: \n");
    for(int k=0; k<nentries; k++)
        printf("%f ",spec[k]);
    double sum = 0.0;
    double* smearedspec = (double*)malloc(nentries*sizeof(double));
    for(int i=0; i<nentries; i++)
    {
        sum += spec[i];
        double* cg = buildConvolvedGauss(e_arr[i], resolution, spec[i], e_arr,
                nentries);
        printf("\n");
        printf("values in the cg\n");
        for(int j = 0; j<nentries;j++)
        {
            if(i == 0)
            {
                smearedspec[j] = cg[j];
                printf("%f ", cg[j]);
           }
            else
                smearedspec[j] += cg[j];
        }
    }
    printf("\n");
    printf("sum of spec: %f \n",sum);    
    return smearedspec;
  }
}
