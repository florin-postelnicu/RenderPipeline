#version 410

#include "Includes/VertexOutput.include"

// Input from the vertex shader
layout(location=0) in VertexOutput vOutput;

// Texture Samplers
uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform sampler2D p3d_Texture2;
uniform sampler2D p3d_Texture3;

// This is required for the materials
#include "Includes/MaterialPacking.include"

uniform float osg_FrameTime;

void main() {

    // Create a material to store the properties on
    Material m;

    vec4 sampledDiffuse = texture(DIFFUSE_TEX, vOutput.texcoord);

    // if (sampledDiffuse.a < 0.5) discard;

    vec4 sampledNormal  = texture(NORMAL_TEX, vOutput.texcoord);
    vec4 sampledSpecular = texture(SPECULAR_TEX, vOutput.texcoord);
    vec4 sampledRoughness = texture(ROUGHNESS_TEX, vOutput.texcoord);

    float bumpFactor = vOutput.materialDiffuse.w;
    float specularFactor = vOutput.materialSpecular.x;
    float metallic = vOutput.materialSpecular.y;
    float roughnessFactor = vOutput.materialSpecular.z;

    vec3 detailNormal = sampledNormal.rgb * 2.0 - 1.0;
    detailNormal = mix(vec3(0,0,1), detailNormal, bumpFactor);
    detailNormal = normalize(detailNormal);

    vec3 normal = vOutput.normalWorld;
    vec3 tangent = vOutput.tangentWorld;
    vec3 binormal = vOutput.binormalWorld;

    vec3 mixedNormal = normalize(
        tangent * detailNormal.x + binormal * detailNormal.y + normal * detailNormal.z
    );

    m.baseColor = sampledDiffuse.rgb * vOutput.materialDiffuse.rgb;
    m.roughness = sampledRoughness.r * roughnessFactor;
    m.specular = sampledSpecular.r * specularFactor;
    m.metallic = metallic;
    m.normal = mixedNormal;
    m.position = vOutput.positionWorld;
    
    renderMaterial(m);
}