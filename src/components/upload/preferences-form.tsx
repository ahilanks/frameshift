"use client";

import { useState, useCallback, useRef } from "react";
import { Plus, X, Upload, Image } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UserPreferences, ProductPlacement } from "@/types";
import { useDropzone } from "react-dropzone";
import { cn } from "@/lib/utils";

interface PreferencesFormProps {
  preferences: UserPreferences;
  onChange: (preferences: UserPreferences) => void;
}

const SAMPLE_PRODUCTS: ProductPlacement[] = [
  {
    id: "iphone-15-pro",
    name: "iPhone 15 Pro",
    description: "Latest flagship smartphone with titanium design",
    category: "Technology",
    imageUrl: "https://via.placeholder.com/100x100?text=iPhone"
  },
  {
    id: "nike-air-max",
    name: "Nike Air Max",
    description: "Premium athletic sneakers for performance",
    category: "Footwear",
    imageUrl: "https://via.placeholder.com/100x100?text=Nike"
  },
  {
    id: "tesla-model-3",
    name: "Tesla Model 3",
    description: "Electric sedan with autopilot capabilities",
    category: "Automotive",
    imageUrl: "https://via.placeholder.com/100x100?text=Tesla"
  }
];

export function PreferencesForm({ preferences, onChange }: PreferencesFormProps) {
  const [newLike, setNewLike] = useState("");
  const [newAudience, setNewAudience] = useState("");
  const [showProductSelector, setShowProductSelector] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addLike = () => {
    if (newLike.trim() && !preferences.likes.includes(newLike.trim())) {
      onChange({
        ...preferences,
        likes: [...preferences.likes, newLike.trim()]
      });
      setNewLike("");
    }
  };

  const removeLike = (like: string) => {
    onChange({
      ...preferences,
      likes: preferences.likes.filter(l => l !== like)
    });
  };

  const addAudience = () => {
    if (newAudience.trim() && !preferences.audience.includes(newAudience.trim())) {
      onChange({
        ...preferences,
        audience: [...preferences.audience, newAudience.trim()]
      });
      setNewAudience("");
    }
  };

  const removeAudience = (audience: string) => {
    onChange({
      ...preferences,
      audience: preferences.audience.filter(a => a !== audience)
    });
  };

  const onImageDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      const imageUrl = URL.createObjectURL(file);
      onChange({
        ...preferences,
        brandImage: file,
        brandImageUrl: imageUrl
      });
    }
  }, [preferences, onChange]);

  const { getRootProps: getImageRootProps, getInputProps: getImageInputProps, isDragActive: isImageDragActive } = useDropzone({
    onDrop: onImageDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp']
    },
    multiple: false
  });

  const removeImage = () => {
    if (preferences.brandImageUrl) {
      URL.revokeObjectURL(preferences.brandImageUrl);
    }
    onChange({
      ...preferences,
      brandImage: undefined,
      brandImageUrl: undefined
    });
  };

  const toggleProduct = (product: ProductPlacement) => {
    const selectedProducts = preferences.selectedProducts || [];
    const isSelected = selectedProducts.some(p => p.id === product.id);

    if (isSelected) {
      onChange({
        ...preferences,
        selectedProducts: selectedProducts.filter(p => p.id !== product.id)
      });
    } else {
      onChange({
        ...preferences,
        selectedProducts: [...selectedProducts, product]
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Brand Preferences */}
      <Card className="xai-card">
        <CardHeader>
          <CardTitle className="text-base xai-text-primary">Brand Names</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex space-x-2">
              <Input
                placeholder="Add brand (e.g., Apple, Nike, Tesla)"
                value={newLike}
                onChange={(e) => setNewLike(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && addLike()}
                className="xai-input"
              />
              <Button onClick={addLike} size="sm" className="xai-button">
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex flex-wrap gap-2">
              {preferences.likes.map((like) => (
                <Badge key={like} variant="secondary" className="flex items-center gap-1 bg-blue-500/20 text-blue-300 border-blue-500/30 hover:bg-blue-500/30" data-testid="brand-badge">
                  {like}
                  <button
                    onClick={() => removeLike(like)}
                    className="text-blue-300 hover:text-blue-100"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Brand Image Upload */}
      <Card className="xai-card">
        <CardHeader>
          <CardTitle className="text-base xai-text-primary">Brand Image (Optional)</CardTitle>
        </CardHeader>
        <CardContent>
          {preferences.brandImageUrl ? (
            <div className="space-y-3" data-testid="uploaded-brand-image">
              <div className="relative w-32 h-32 rounded-lg overflow-hidden border border-blue-500/30">
                <img
                  src={preferences.brandImageUrl}
                  alt="Brand reference"
                  className="w-full h-full object-cover"
                />
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={removeImage}
                  className="absolute top-2 right-2 bg-red-500/80 hover:bg-red-500"
                  data-testid="remove-brand-image-btn"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-sm xai-text-secondary">
                Brand reference image uploaded. AI will use this for context.
              </p>
            </div>
          ) : (
            <div
              {...getImageRootProps()}
              data-testid="brand-image-dropzone"
              className={cn(
                "border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors",
                isImageDragActive
                  ? "border-blue-400 bg-blue-500/10 scale-105"
                  : "border-white/30 hover:border-blue-400 hover:bg-blue-500/5 hover:scale-105"
              )}
            >
              <input {...getImageInputProps()} />
              <div className="space-y-2">
                <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center mx-auto">
                  <Image className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <p className="text-sm font-medium xai-text-primary">
                    Upload brand image
                  </p>
                  <p className="text-xs xai-text-muted">
                    PNG, JPG up to 10MB (optional)
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Product Selection (Optional) */}
      <Card className="xai-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base xai-text-primary">Specific Products (Optional)</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowProductSelector(!showProductSelector)}
              className="border-white/30 text-white hover:bg-white/10"
            >
              {showProductSelector ? "Hide" : "Show"} Products
            </Button>
          </div>
        </CardHeader>
        {showProductSelector && (
          <CardContent>
            <div className="space-y-3">
              <p className="text-sm xai-text-secondary">
                Choose specific products instead of letting AI auto-select from brands
              </p>
              <div className="grid grid-cols-1 gap-3">
                {SAMPLE_PRODUCTS.map((product) => {
                  const isSelected = preferences.selectedProducts?.some(p => p.id === product.id) || false;
                  return (
                    <div
                      key={product.id}
                      onClick={() => toggleProduct(product)}
                      className={cn(
                        "flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors xai-hover",
                        isSelected
                          ? "border-blue-500/50 bg-blue-500/20"
                          : "border-white/20 hover:border-white/30"
                      )}
                      data-testid={isSelected ? "selected-product" : "unselected-product"}
                    >
                      <img
                        src={product.imageUrl}
                        alt={product.name}
                        className="w-12 h-12 rounded-lg object-cover"
                      />
                      <div className="flex-1">
                        <h4 className="font-medium xai-text-primary">{product.name}</h4>
                        <p className="text-sm xai-text-secondary">{product.description}</p>
                        <Badge variant="outline" className="mt-1 text-xs border-blue-500/30 text-blue-300">
                          {product.category}
                        </Badge>
                      </div>
                      {isSelected && (
                        <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                          <div className="w-2 h-2 bg-white rounded-full" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {preferences.selectedProducts && preferences.selectedProducts.length > 0 && (
                <div className="mt-4 p-3 bg-green-500/20 rounded-lg border border-green-500/30">
                  <p className="text-sm text-green-400 font-medium">
                    Selected Products: {preferences.selectedProducts.map(p => p.name).join(', ')}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Audience Preferences */}
      <Card className="xai-card">
        <CardHeader>
          <CardTitle className="text-base xai-text-primary">Target Audience (Optional)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex space-x-2">
              <Input
                placeholder="Add audience (e.g., Young professionals, Gamers)"
                value={newAudience}
                onChange={(e) => setNewAudience(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && addAudience()}
                className="xai-input"
              />
              <Button onClick={addAudience} size="sm" className="xai-button">
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex flex-wrap gap-2">
              {preferences.audience.map((audience) => (
                <Badge key={audience} variant="outline" className="flex items-center gap-1 bg-purple-500/20 text-purple-300 border-purple-500/30 hover:bg-purple-500/30" data-testid="audience-badge">
                  {audience}
                  <button
                    onClick={() => removeAudience(audience)}
                    className="text-purple-300 hover:text-purple-100"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      <Card className="border-cyan-500/30 bg-cyan-500/10 xai-card">
        <CardContent className="pt-6">
          <h3 className="font-medium text-cyan-400 mb-3">Configuration Summary</h3>
          <div className="space-y-2 text-sm text-cyan-300">
            <div className="flex justify-between">
              <span>Brand Names:</span>
              <span className="font-medium">
                {preferences.likes.length > 0 ? preferences.likes.join(', ') : 'Auto-generate from AI'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Brand Image:</span>
              <span className="font-medium">
                {preferences.brandImageUrl ? 'Uploaded' : 'None (AI will select)'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Specific Products:</span>
              <span className="font-medium">
                {preferences.selectedProducts?.length || 0} selected
              </span>
            </div>
            <div className="flex justify-between">
              <span>Target Audience:</span>
              <span className="font-medium">
                {preferences.audience.length > 0 ? preferences.audience.join(', ') : 'General'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}