using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using UnityEngine;

public enum ImplementationType
{
    UseCoroutine,
    UseAsync
}

public class VideoStreamingClient : MonoBehaviour
{
    public MeshRenderer frame;
    public string ServerUrl = "http://localhost:8000/mjpg";
    public ImplementationType ImplementationType;
    public bool IsRunning { get; private set; }

    private Texture2D texture;
    private bool shutdown;
    private CoroutineContext coroutineContext;
    private AsyncContext asyncContext;

    private abstract class Context : IDisposable
    {
        public abstract void Dispose();
    }

    private class CoroutineContext : Context
    {
        private bool disposed;
        public HttpWebRequest HttpWebRequest { get; set; }
        public HttpWebResponse HttpWebResponse { get; set; }
        public Stream HttpResponseStream { get; set; }
        public string Boundary { get; set; }

        public override void Dispose()
        {
            if (this.disposed)
            {
                return;
            }
            this.HttpResponseStream.Dispose();
            this.HttpWebResponse.Close();
            this.disposed = true;
        }
    }

    private class AsyncContext : Context
    {
        public byte[] JPG { get; set; }
        public object LockObject { get; } = new object();
        public HttpWebRequest HttpWebRequest { get; set; }

        public override void Dispose()
        {
        }
    }

    void Start()
    {
        this.texture = new Texture2D(2, 2);
        switch (this.ImplementationType)
        {
            case ImplementationType.UseCoroutine:
                {
                    var ctx = new CoroutineContext();
                    ctx.HttpWebRequest = (HttpWebRequest)WebRequest.Create(this.ServerUrl);
                    ctx.HttpWebResponse = (HttpWebResponse)ctx.HttpWebRequest.GetResponse();
                    ctx.HttpResponseStream = ctx.HttpWebResponse.GetResponseStream();
                    ctx.Boundary = GetBoundary(ctx.HttpWebResponse);
                    this.coroutineContext = ctx;
                    this.StartCoroutine(this.GetFrame());
                    break;
                }
            case ImplementationType.UseAsync:
                {
                    var ctx = new AsyncContext();
                    ctx.HttpWebRequest = (HttpWebRequest)WebRequest.Create(this.ServerUrl);
                    ctx.HttpWebRequest.BeginGetResponse(OnGetResponse, ctx);
                    this.asyncContext = ctx;
                    break;
                }
        }
    }

    void Update()
    {
        if (this.ImplementationType == ImplementationType.UseAsync)
        {
            lock (this.asyncContext.LockObject)
            {
                if (this.asyncContext.JPG != null)
                {
                    this.texture.LoadImage(this.asyncContext.JPG);
                    this.frame.material.mainTexture = texture;
                    this.asyncContext.JPG = null;
                }
            }
        }
    }
    private void OnDisable()
    {
        this.shutdown = true;
        this.coroutineContext?.Dispose();
        this.asyncContext?.Dispose();
    }

    private void OnGetResponse(IAsyncResult asyncResult)
    {
        try
        {
            this.IsRunning = true;
            var ctx = (AsyncContext)asyncResult.AsyncState;

            var httpWebResponse = (HttpWebResponse)ctx.HttpWebRequest.EndGetResponse(asyncResult);
            var boundary = GetBoundary(httpWebResponse);

            using (var httpResponseStream = httpWebResponse.GetResponseStream())
            {
                while (!this.shutdown)
                {
                    int bytesToRead = GetContentLength(httpResponseStream, boundary);
                    if (bytesToRead == -1)
                    {
                        continue;
                    }

                    var jpg = new byte[bytesToRead];
                    var leftToRead = bytesToRead;
                    while (!this.shutdown && leftToRead > 0)
                    {
                        leftToRead -= httpResponseStream.Read(jpg, bytesToRead - leftToRead, leftToRead);
                    }

                    if (this.shutdown)
                    {
                        break;
                    }

                    //read cr/lf
                    httpResponseStream.ReadByte();
                    httpResponseStream.ReadByte();

                    lock (ctx.LockObject)
                    {
                        ctx.JPG = jpg;
                    }
                }
            }

            httpWebResponse.Close();
        }
        catch (Exception ex)
        {
            Debug.LogError(ex);
        }
        finally
        {
            this.IsRunning = false;
        }
    }

    private IEnumerator GetFrame()
    {
        while (true)
        {
            int bytesToRead = GetContentLength(this.coroutineContext.HttpResponseStream, this.coroutineContext.Boundary);
            if (bytesToRead == -1)
            {
                yield break;
            }

            var jpg = new byte[bytesToRead];
            var leftToRead = bytesToRead;
            while (leftToRead > 0)
            {
                leftToRead -= this.coroutineContext.HttpResponseStream.Read(jpg, bytesToRead - leftToRead, leftToRead);
                yield return null;
            }

            this.texture.LoadImage(jpg);
            this.frame.material.mainTexture = texture;

            //read cr/lf
            this.coroutineContext.HttpResponseStream.ReadByte();
            this.coroutineContext.HttpResponseStream.ReadByte();
        }
    }


    static int GetContentLength(Stream stream, string boundary)
    {
        var contentLength = -1;
        var line = "";
        var atEOL = false;

        int b;
        while ((b = stream.ReadByte()) != -1)
        {
            if (b == 10)
            {
                continue;
            }
            if (b == 13)
            {
                if (atEOL)
                {
                    stream.ReadByte();
                    return contentLength;
                }
                if (boundary != null && line.StartsWith(boundary, StringComparison.Ordinal))
                {
                    //boundary
                }
                else if (line.StartsWith("Content-length:"))
                {
                    contentLength = Convert.ToInt32(line.Substring("Content-length:".Length).Trim());
                }

                line = "";
                atEOL = true;
            }
            else
            {
                atEOL = false;
                line += (char)b;
            }
        }

        return -1;
    }

    private static string GetBoundary(HttpWebResponse httpWebResponse)
    {
        var contentType = httpWebResponse.Headers["Content-Type"];

        if (string.IsNullOrEmpty(contentType) || !contentType.Contains("="))
        {
            throw new Exception("Invalid Content-Type http header");
        }

        var pEq = contentType.IndexOf("=");
        var boundary = contentType.Substring(pEq + 1).Replace("\"", "");
        if (!boundary.StartsWith("--"))
        {
            boundary = "--" + boundary;
        }

        //var boundaryBytes = Encoding.UTF8.GetBytes(this.boundary);
        return boundary;
    }
}
