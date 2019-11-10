using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class RotateCube : MonoBehaviour
{
    public float speed = 0.5f;

    void Start()
    {
        
    }

    void Update()
    {
        if (Input.GetKey(KeyCode.Escape))
        {
            Application.Quit();
        }

        if (Input.GetKey(KeyCode.RightArrow))
        {
            this.transform.Rotate(new Vector3(0, -this.speed, 0));
        }

        if (Input.GetKey(KeyCode.LeftArrow))
        {
            this.transform.Rotate(new Vector3(0, this.speed, 0));
        }

        if (Input.GetKey(KeyCode.DownArrow))
        {
            this.transform.Rotate(new Vector3(this.speed, 0, 0));
        }

        if (Input.GetKey(KeyCode.UpArrow))
        {
            this.transform.Rotate(new Vector3(-this.speed, 0, 0));
        }

    }
}
