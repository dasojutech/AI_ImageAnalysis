import geopandas as gpd
import rasterio
from rasterio.features import rasterize
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt

# ----------- Config -------------
raster_path = r"C:\projects\image_analysis\AI_ImageAnalysis\data\vectors\san_francisco_imagery.tif"
vector_path = r"C:\projects\image_analysis\AI_ImageAnalysis\data\vectors\sf_buildings.geojson"
patch_size = 256
batch_size = 4
epochs = 5
lr = 1e-3
device = 'cuda' if torch.cuda.is_available() else 'cpu'
# --------------------------------

# ----------- Load Data -----------
raster = rasterio.open(raster_path)
buildings = gpd.read_file(vector_path)

mask = rasterize(
    [(geom, 1) for geom in buildings.geometry],
    out_shape=(raster.height, raster.width),
    transform=raster.transform,
    fill=0,
    dtype='uint8'
)

image = raster.read().astype(np.float32)
image = (image - image.min()) / (image.max() - image.min())

image_tensor = torch.tensor(image)
mask_tensor = torch.tensor(mask).unsqueeze(0)
# ---------------------------------

# ----------- Dataset --------------
class GeoDataset(Dataset):
    def __init__(self, image, mask, patch_size=256):
        self.image = image
        self.mask = mask
        self.patch_size = patch_size
        self.height, self.width = mask.shape

        self.rows = self.height // patch_size
        self.cols = self.width // patch_size

    def __len__(self):
        return self.rows * self.cols

    def __getitem__(self, idx):
        i = (idx // self.cols) * self.patch_size
        j = (idx % self.cols) * self.patch_size

        img_patch = self.image[:, i:i+self.patch_size, j:j+self.patch_size]
        mask_patch = self.mask[i:i+self.patch_size, j:j+self.patch_size]

        return img_patch, mask_patch.unsqueeze(0)

dataset = GeoDataset(image_tensor, mask_tensor[0], patch_size)
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
# ---------------------------------

# ----------- UNet Model -----------
class UNet(nn.Module):
    def __init__(self, in_channels=3, out_channels=1):
        super().__init__()

        self.enc1 = nn.Sequential(
            nn.Conv2d(in_channels, 16, 3, padding=1), nn.ReLU(),
            nn.Conv2d(16, 16, 3, padding=1), nn.ReLU()
        )

        self.enc2 = nn.Sequential(
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1), nn.ReLU()
        )

        self.pool = nn.MaxPool2d(2, 2)

        self.up = nn.ConvTranspose2d(32, 16, 2, stride=2)

        self.dec1 = nn.Sequential(
            nn.Conv2d(32, 16, 3, padding=1), nn.ReLU(),
            nn.Conv2d(16, 16, 3, padding=1), nn.ReLU()
        )

        self.outc = nn.Conv2d(16, out_channels, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))

        d1 = self.up(e2)
        d1 = torch.cat([d1, e1], dim=1)

        out = self.outc(self.dec1(d1))
        return out  # logits

model = UNet(in_channels=image_tensor.shape[0]).to(device)
# ---------------------------------

# ----------- Training --------------
optimizer = torch.optim.Adam(model.parameters(), lr=lr)
criterion = nn.BCEWithLogitsLoss()

for epoch in range(epochs):
    model.train()
    total_loss = 0

    for imgs, masks in dataloader:
        imgs = imgs.to(device)
        masks = masks.to(device).float()

        optimizer.zero_grad()
        outputs = model(imgs)

        loss = criterion(outputs, masks)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.4f}")
# ---------------------------------

# ----------- Full Prediction -------
model.eval()
full_pred = np.zeros((raster.height, raster.width))

with torch.no_grad():
    for i in range(0, raster.height, patch_size):
        for j in range(0, raster.width, patch_size):

            patch = image_tensor[:, i:i+patch_size, j:j+patch_size]

            if patch.shape[1] != patch_size or patch.shape[2] != patch_size:
                continue

            patch = patch.unsqueeze(0).to(device)
            pred = torch.sigmoid(model(patch))[0,0].cpu().numpy()

            full_pred[i:i+patch_size, j:j+patch_size] = pred
# ---------------------------------

# ----------- Visualization --------
plt.figure(figsize=(15,5))

plt.subplot(1,3,1)
plt.imshow(np.transpose(image, (1,2,0)))
plt.title("Full Image")

plt.subplot(1,3,2)
plt.imshow(mask, cmap='gray')
plt.title("Ground Truth")

plt.subplot(1,3,3)
plt.imshow(full_pred > 0.5, cmap='gray')
plt.title("Predicted Buildings")

plt.show()
# ---------------------------------