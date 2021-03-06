#ifndef __PYX_HAVE__gevent__ares
#define __PYX_HAVE__gevent__ares

struct PyGeventAresChannelObject;

/* "gevent/ares.pyx":235
 * 
 * 
 * cdef public class channel [object PyGeventAresChannelObject, type PyGeventAresChannel_Type]:             # <<<<<<<<<<<<<<
 * 
 *     cdef public object loop
 */
struct PyGeventAresChannelObject {
  PyObject_HEAD
  struct __pyx_vtabstruct_6gevent_4ares_channel *__pyx_vtab;
  PyObject *loop;
  struct ares_channeldata *channel;
  PyObject *_watchers;
  PyObject *_timer;
};

#ifndef __PYX_HAVE_API__gevent__ares

#ifndef __PYX_EXTERN_C
  #ifdef __cplusplus
    #define __PYX_EXTERN_C extern "C"
  #else
    #define __PYX_EXTERN_C extern
  #endif
#endif

__PYX_EXTERN_C DL_IMPORT(PyTypeObject) PyGeventAresChannel_Type;

#endif /* !__PYX_HAVE_API__gevent__ares */

#if PY_MAJOR_VERSION < 3
PyMODINIT_FUNC initares(void);
#else
PyMODINIT_FUNC PyInit_ares(void);
#endif

#endif /* !__PYX_HAVE__gevent__ares */
